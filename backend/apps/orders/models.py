import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from apps.catalog.models import Product
from apps.core.models import TimestampedUUIDModel
from apps.stores.models import Store


class Customer(TimestampedUUIDModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="customers")
    phone = models.CharField(max_length=32)
    email = models.EmailField(blank=True)
    name = models.CharField(max_length=150, blank=True)
    last_delivery_address = models.TextField(blank=True)
    order_count = models.PositiveIntegerField(default=0)
    last_order_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-last_order_at", "phone")
        constraints = [
            models.UniqueConstraint(fields=("store", "phone"), name="customer_store_phone_unique")
        ]
        indexes = [models.Index(fields=("store", "phone"), name="customer_store_phone_idx")]

    def __str__(self) -> str:
        return f"{self.store}: {self.phone}"


class Order(TimestampedUUIDModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for delivery"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    store = models.ForeignKey(Store, on_delete=models.PROTECT, related_name="orders")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    public_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    idempotency_key = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING)
    customer_name = models.CharField(max_length=150, blank=True)
    phone_snapshot = models.CharField(max_length=32)
    email_snapshot = models.EmailField(blank=True)
    delivery_address = models.TextField()
    delivery_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_distance_miles = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    notes = models.TextField(blank=True)
    currency = models.CharField(max_length=3)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    status_changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("store", "idempotency_key"),
                condition=~Q(idempotency_key=""),
                name="order_store_idempotency_unique",
            ),
            models.CheckConstraint(condition=Q(subtotal__gte=0), name="order_subtotal_nonnegative"),
            models.CheckConstraint(condition=Q(delivery_fee__gte=0), name="order_delivery_fee_nonnegative"),
            models.CheckConstraint(condition=Q(total__gte=0), name="order_total_nonnegative"),
        ]
        indexes = [
            models.Index(fields=("store", "created_at"), name="order_store_created_idx"),
            models.Index(fields=("store", "status", "created_at"), name="order_store_status_created_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.store} order {self.id}"


class OrderItem(TimestampedUUIDModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        related_name="order_items",
        null=True,
        blank=True,
    )
    product_name = models.CharField(max_length=180)
    sku = models.CharField(max_length=80, blank=True)
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ("created_at",)
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="order_item_quantity_positive"),
            models.CheckConstraint(condition=Q(unit_price__gte=0), name="order_item_price_nonnegative"),
            models.CheckConstraint(condition=Q(line_total__gte=0), name="order_item_total_nonnegative"),
        ]

    def __str__(self) -> str:
        return f"{self.product_name} x {self.quantity}"

