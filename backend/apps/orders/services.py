from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from apps.catalog.models import Product
from apps.orders.models import Customer, Order, OrderItem
from apps.orders.distance import distance_miles
from apps.orders.phone import normalize_phone
from apps.stores.models import Store


@dataclass(frozen=True, slots=True)
class CheckoutItem:
    product_id: UUID
    quantity: int


@dataclass(frozen=True, slots=True)
class CheckoutCommand:
    phone: str
    customer_name: str
    delivery_address: str
    notes: str
    items: tuple[CheckoutItem, ...]
    email: str = ""
    delivery_latitude: Decimal | None = None
    delivery_longitude: Decimal | None = None
    idempotency_key: str = ""


def place_order(*, store: Store, command: CheckoutCommand) -> tuple[Order, bool]:
    try:
        with transaction.atomic():
            return _place_order(store=store, command=command)
    except IntegrityError:
        if command.idempotency_key:
            existing = Order.objects.filter(
                store=store,
                idempotency_key=command.idempotency_key,
            ).first()
            if existing:
                return existing, False
        raise


def _place_order(*, store: Store, command: CheckoutCommand) -> tuple[Order, bool]:
    if store.status != Store.Status.ACTIVE:
        raise ValidationError("This store is not accepting orders.")
    if command.idempotency_key:
        existing = Order.objects.filter(
            store=store,
            idempotency_key=command.idempotency_key,
        ).first()
        if existing:
            return existing, False

    delivery_distance = None
    if store.delivery_radius_enabled:
        if store.latitude is None or store.longitude is None:
            raise ValidationError("This store's delivery zone is not configured correctly.")
        if command.delivery_latitude is None or command.delivery_longitude is None:
            raise ValidationError(
                {"delivery_location": "Select your delivery location before placing the order."}
            )
        delivery_distance = distance_miles(
            origin_latitude=store.latitude,
            origin_longitude=store.longitude,
            destination_latitude=command.delivery_latitude,
            destination_longitude=command.delivery_longitude,
        )
        if delivery_distance > store.delivery_radius_miles:
            raise ValidationError(
                {
                    "delivery_location": (
                        f"This address is {delivery_distance} miles from the store; "
                        f"delivery is limited to {store.delivery_radius_miles} miles."
                    )
                }
            )

    quantities: dict[UUID, int] = {}
    for item in command.items:
        if item.quantity <= 0:
            raise ValidationError("Item quantities must be positive.")
        quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity
    if not quantities:
        raise ValidationError("At least one order item is required.")

    products = list(
        Product.objects.select_for_update()
        .filter(store=store, id__in=quantities)
        .select_related("category")
    )
    products_by_id = {product.id: product for product in products}
    missing = set(quantities) - set(products_by_id)
    if missing:
        raise ValidationError({"items": "One or more products do not exist in this store."})

    subtotal = Decimal("0.00")
    order_items = []
    inventory_updates = []
    now = timezone.now()
    for product_id, quantity in quantities.items():
        product = products_by_id[product_id]
        if not product.is_active or (product.category_id and not product.category.is_active):
            raise ValidationError({"items": f"{product.name} is not available."})
        if product.track_inventory:
            if product.stock_quantity < quantity:
                raise ValidationError({"items": f"Insufficient stock for {product.name}."})
            product.stock_quantity -= quantity
            product.updated_at = now
            inventory_updates.append(product)
        line_total = product.price * quantity
        subtotal += line_total
        order_items.append(
            OrderItem(
                product=product,
                product_name=product.name,
                sku=product.sku,
                unit_price=product.price,
                quantity=quantity,
                line_total=line_total,
            )
        )

    phone = normalize_phone(command.phone)
    email = command.email.strip().lower()
    customer, _ = Customer.objects.get_or_create(store=store, phone=phone)
    customer.name = command.customer_name or customer.name
    customer.email = email or customer.email
    customer.last_delivery_address = command.delivery_address
    customer.save(update_fields=("name", "email", "last_delivery_address", "updated_at"))

    order = Order.objects.create(
        store=store,
        customer=customer,
        idempotency_key=command.idempotency_key,
        customer_name=command.customer_name,
        phone_snapshot=phone,
        email_snapshot=customer.email,
        delivery_address=command.delivery_address,
        delivery_latitude=command.delivery_latitude,
        delivery_longitude=command.delivery_longitude,
        delivery_distance_miles=delivery_distance,
        notes=command.notes,
        currency=store.currency,
        subtotal=subtotal,
        delivery_fee=store.delivery_fee,
        total=subtotal + store.delivery_fee,
    )
    for item in order_items:
        item.order = order
    OrderItem.objects.bulk_create(order_items)
    if inventory_updates:
        Product.objects.bulk_update(inventory_updates, ("stock_quantity", "updated_at"))
    Customer.objects.filter(pk=customer.pk).update(
        order_count=F("order_count") + 1,
        last_order_at=now,
    )
    return order, True


ALLOWED_STATUS_TRANSITIONS = {
    Order.Status.PENDING: {Order.Status.CONFIRMED, Order.Status.CANCELLED},
    Order.Status.CONFIRMED: {Order.Status.PREPARING, Order.Status.CANCELLED},
    Order.Status.PREPARING: {Order.Status.READY, Order.Status.CANCELLED},
    Order.Status.READY: {Order.Status.OUT_FOR_DELIVERY, Order.Status.COMPLETED, Order.Status.CANCELLED},
    Order.Status.OUT_FOR_DELIVERY: {Order.Status.COMPLETED, Order.Status.CANCELLED},
    Order.Status.COMPLETED: set(),
    Order.Status.CANCELLED: set(),
}


@transaction.atomic
def transition_order(*, order: Order, target_status: str) -> Order:
    locked = Order.objects.select_for_update().get(pk=order.pk)
    allowed = ALLOWED_STATUS_TRANSITIONS[locked.status]
    if target_status not in allowed:
        raise ValidationError(
            {"status": f"Cannot transition from {locked.status} to {target_status}."}
        )

    if target_status == Order.Status.CANCELLED:
        items = list(locked.items.all())
        product_ids = [item.product_id for item in items if item.product_id]
        locked_products = {
            product.id: product
            for product in Product.objects.select_for_update().filter(id__in=product_ids)
        }
        products = []
        now = timezone.now()
        for item in items:
            product = locked_products.get(item.product_id)
            if product and product.track_inventory:
                product.stock_quantity += item.quantity
                product.updated_at = now
                products.append(product)
        if products:
            Product.objects.bulk_update(products, ("stock_quantity", "updated_at"))

    locked.status = target_status
    locked.status_changed_at = timezone.now()
    locked.save(update_fields=("status", "status_changed_at", "updated_at"))
    return locked

