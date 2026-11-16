import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError

from apps.catalog.tests.factories import make_product
from apps.orders.models import Customer, Order
from apps.orders.services import (
    CheckoutCommand,
    CheckoutItem,
    place_order,
    transition_order,
)
from apps.stores.tests.factories import make_store


@pytest.mark.django_db
def test_checkout_normalizes_phone_snapshots_price_and_deducts_stock():
    store = make_store(name="Green Mart", slug="green-mart")
    product = make_product(store=store, track_inventory=True, stock_quantity=5)

    order, created = place_order(
        store=store,
        command=CheckoutCommand(
            phone="0300 1234567",
            email="CUSTOMER@Example.com ",
            customer_name="A Customer",
            delivery_address="Street 1",
            notes="Leave at door",
            items=(CheckoutItem(product_id=product.id, quantity=2),),
        ),
    )

    assert created is True
    assert order.phone_snapshot == "+923001234567"
    assert order.email_snapshot == "customer@example.com"
    assert order.items.get().unit_price == product.price
    assert order.total == product.price * 2 + store.delivery_fee
    product.refresh_from_db()
    assert product.stock_quantity == 3
    customer = Customer.objects.get(store=store)
    assert customer.order_count == 1
    assert customer.email == "customer@example.com"


@pytest.mark.django_db
def test_checkout_idempotency_does_not_duplicate_order_or_stock_change():
    store = make_store(name="Green Mart", slug="green-mart")
    product = make_product(store=store, track_inventory=True, stock_quantity=5)
    command = CheckoutCommand(
        phone="+923001234567",
        customer_name="Customer",
        delivery_address="Street 1",
        notes="",
        items=(CheckoutItem(product_id=product.id, quantity=2),),
        idempotency_key="checkout-1",
    )

    first, first_created = place_order(store=store, command=command)
    second, second_created = place_order(store=store, command=command)

    assert first.id == second.id
    assert first_created is True
    assert second_created is False
    assert Order.objects.count() == 1
    product.refresh_from_db()
    assert product.stock_quantity == 3


@pytest.mark.django_db
def test_insufficient_stock_rolls_back_checkout():
    store = make_store(name="Green Mart", slug="green-mart")
    product = make_product(store=store, track_inventory=True, stock_quantity=1)

    with pytest.raises(ValidationError):
        place_order(
            store=store,
            command=CheckoutCommand(
                phone="+923001234567",
                customer_name="Customer",
                delivery_address="Street 1",
                notes="",
                items=(CheckoutItem(product_id=product.id, quantity=2),),
            ),
        )

    assert not Order.objects.exists()
    assert not Customer.objects.exists()


@pytest.mark.django_db
def test_cancellation_restores_inventory_and_terminal_status_cannot_change():
    store = make_store(name="Green Mart", slug="green-mart")
    product = make_product(store=store, track_inventory=True, stock_quantity=5)
    order = place_order(
        store=store,
        command=CheckoutCommand(
            phone="+923001234567",
            customer_name="Customer",
            delivery_address="Street 1",
            notes="",
            items=(CheckoutItem(product_id=product.id, quantity=2),),
        ),
    )[0]

    cancelled = transition_order(order=order, target_status=Order.Status.CANCELLED)
    product.refresh_from_db()
    assert cancelled.status == Order.Status.CANCELLED
    assert product.stock_quantity == 5

    with pytest.raises(ValidationError):
        transition_order(order=cancelled, target_status=Order.Status.CONFIRMED)


@pytest.mark.django_db
def test_checkout_enforces_store_delivery_radius_and_saves_distance():
    store = make_store(name="Local Mart", slug="local-mart")
    store.latitude = Decimal("31.520400")
    store.longitude = Decimal("74.358700")
    store.delivery_radius_miles = Decimal("1.00")
    store.delivery_radius_enabled = True
    store.save()
    product = make_product(store=store)

    order, _ = place_order(
        store=store,
        command=CheckoutCommand(
            phone="+923001234567",
            customer_name="Nearby Customer",
            delivery_address="Nearby address",
            delivery_latitude=Decimal("31.525000"),
            delivery_longitude=Decimal("74.358700"),
            notes="",
            items=(CheckoutItem(product_id=product.id, quantity=1),),
        ),
    )

    assert order.delivery_distance_miles is not None
    assert order.delivery_distance_miles < Decimal("1.00")

    with pytest.raises(ValidationError, match="delivery is limited"):
        place_order(
            store=store,
            command=CheckoutCommand(
                phone="+923009999999",
                customer_name="Distant Customer",
                delivery_address="Distant address",
                delivery_latitude=Decimal("31.550000"),
                delivery_longitude=Decimal("74.358700"),
                notes="",
                items=(CheckoutItem(product_id=product.id, quantity=1),),
            ),
        )


@pytest.mark.django_db
def test_checkout_requires_coordinates_when_delivery_radius_is_enabled():
    store = make_store(name="Local Mart", slug="local-mart")
    store.latitude = Decimal("31.520400")
    store.longitude = Decimal("74.358700")
    store.delivery_radius_enabled = True
    store.save()
    product = make_product(store=store)

    with pytest.raises(ValidationError, match="Select your delivery location"):
        place_order(
            store=store,
            command=CheckoutCommand(
                phone="+923001234567",
                customer_name="Customer",
                delivery_address="Address",
                notes="",
                items=(CheckoutItem(product_id=product.id, quantity=1),),
            ),
        )


@pytest.mark.django_db
def test_checkout_cannot_combine_products_from_different_stores():
    checkout_store = make_store(name="First Store", slug="first-store")
    other_store = make_store(name="Second Store", slug="second-store")
    other_product = make_product(store=other_store)

    with pytest.raises(ValidationError, match="do not exist in this store"):
        place_order(
            store=checkout_store,
            command=CheckoutCommand(
                phone="+923001234567",
                customer_name="Customer",
                delivery_address="Address",
                notes="",
                items=(CheckoutItem(product_id=other_product.id, quantity=1),),
            ),
        )

    assert not Order.objects.exists()

