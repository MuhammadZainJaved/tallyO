from apps.orders.services import CheckoutCommand, CheckoutItem, place_order


def make_order(*, store, product, phone="+923001234567", quantity=1, idempotency_key=""):
    return place_order(
        store=store,
        command=CheckoutCommand(
            phone=phone,
            customer_name="Customer",
            delivery_address="Street 1",
            notes="",
            items=(CheckoutItem(product_id=product.id, quantity=quantity),),
            idempotency_key=idempotency_key,
        ),
    )[0]

