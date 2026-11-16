import pytest
from rest_framework.test import APIClient

from apps.catalog.tests.factories import make_product
from apps.orders.models import Order
from apps.orders.tests.factories import make_order
from apps.stores.tests.factories import make_store, make_user


@pytest.mark.django_db
def test_guest_can_checkout_and_lookup_order_by_public_token():
    store = make_store(name="Green Mart", slug="green-mart")
    product = make_product(store=store)
    client = APIClient()

    response = client.post(
        "/api/v1/storefront/green-mart/orders/",
        {
            "phone": "+923001234567",
            "email": "customer@example.com",
            "customer_name": "Customer",
            "delivery_address": "Street 1",
            "items": [{"product_id": str(product.id), "quantity": 1}],
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY="browser-attempt-1",
    )

    assert response.status_code == 201
    lookup = client.get(
        f"/api/v1/storefront/green-mart/orders/{response.json()['public_token']}/"
    )
    assert lookup.status_code == 200
    assert lookup.json()["status"] == Order.Status.PENDING


@pytest.mark.django_db
def test_store_admin_can_update_own_customer_but_not_another_store_customer():
    admin = make_user(email="admin@example.com")
    own_store = make_store(name="Own", slug="own", admin=admin)
    other_store = make_store(name="Other", slug="other")
    own_order = make_order(store=own_store, product=make_product(store=own_store))
    other_order = make_order(
        store=other_store,
        product=make_product(store=other_store, slug="other-product"),
        phone="+923009999999",
    )
    client = APIClient()
    client.force_authenticate(admin)

    updated = client.patch(
        f"/api/v1/stores/{own_store.id}/customers/{own_order.customer_id}/",
        {"name": "Updated Customer", "email": "updated@example.com"},
        format="json",
    )
    denied = client.patch(
        f"/api/v1/stores/{other_store.id}/customers/{other_order.customer_id}/",
        {"name": "Not Allowed"},
        format="json",
    )

    assert updated.status_code == 200
    assert updated.json()["email"] == "updated@example.com"
    assert denied.status_code == 404


@pytest.mark.django_db
def test_store_admin_only_lists_own_orders():
    admin = make_user(email="admin@example.com")
    own_store = make_store(name="Own", slug="own", admin=admin)
    other_store = make_store(name="Other", slug="other")
    own_order = make_order(store=own_store, product=make_product(store=own_store))
    make_order(store=other_store, product=make_product(store=other_store, slug="other-product"))
    client = APIClient()
    client.force_authenticate(admin)

    response = client.get(f"/api/v1/stores/{own_store.id}/orders/")
    denied = client.get(f"/api/v1/stores/{other_store.id}/orders/")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["results"]] == [str(own_order.id)]
    assert denied.status_code == 404


@pytest.mark.django_db
def test_store_admin_can_transition_own_order():
    admin = make_user(email="admin@example.com")
    store = make_store(name="Own", slug="own", admin=admin)
    order = make_order(store=store, product=make_product(store=store))
    client = APIClient()
    client.force_authenticate(admin)

    response = client.post(
        f"/api/v1/stores/{store.id}/orders/{order.id}/transition/",
        {"status": Order.Status.CONFIRMED},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["status"] == Order.Status.CONFIRMED

