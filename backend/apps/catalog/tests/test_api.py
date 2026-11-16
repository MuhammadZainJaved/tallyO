import pytest
from rest_framework.test import APIClient

from apps.catalog.tests.factories import make_category, make_product
from apps.stores.tests.factories import make_store, make_user


@pytest.mark.django_db
def test_store_admin_can_manage_own_catalog():
    admin = make_user(email="admin@example.com")
    store = make_store(name="Green Mart", slug="green-mart", admin=admin)
    client = APIClient()
    client.force_authenticate(admin)

    category_response = client.post(
        f"/api/v1/stores/{store.id}/categories/",
        {"name": "Dairy", "slug": "dairy"},
        format="json",
    )
    assert category_response.status_code == 201

    product_response = client.post(
        f"/api/v1/stores/{store.id}/products/",
        {
            "name": "Milk",
            "slug": "milk",
            "category": category_response.json()["id"],
            "price": "250.00",
            "track_inventory": True,
            "stock_quantity": 5,
        },
        format="json",
    )
    assert product_response.status_code == 201
    assert product_response.json()["category_name"] == "Dairy"


@pytest.mark.django_db
def test_admin_cannot_use_category_from_another_store():
    admin = make_user(email="admin@example.com")
    own_store = make_store(name="Own", slug="own", admin=admin)
    other_store = make_store(name="Other", slug="other")
    other_category = make_category(store=other_store)
    client = APIClient()
    client.force_authenticate(admin)

    response = client.post(
        f"/api/v1/stores/{own_store.id}/products/",
        {
            "name": "Milk",
            "slug": "milk",
            "category": str(other_category.id),
            "price": "250.00",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "category" in response.json()["error"]["details"]


@pytest.mark.django_db
def test_admin_cannot_list_another_store_catalog():
    admin = make_user(email="admin@example.com")
    make_store(name="Own", slug="own", admin=admin)
    other_store = make_store(name="Other", slug="other")
    client = APIClient()
    client.force_authenticate(admin)

    response = client.get(f"/api/v1/stores/{other_store.id}/products/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_public_catalog_hides_inactive_products_and_categories():
    store = make_store(name="Green Mart", slug="green-mart")
    active_category = make_category(store=store, name="Dairy", slug="dairy")
    inactive_category = make_category(store=store, name="Hidden", slug="hidden", is_active=False)
    visible = make_product(store=store, category=active_category, name="Milk", slug="milk")
    uncategorized = make_product(store=store, name="Bag", slug="bag")
    make_product(store=store, category=inactive_category, name="Hidden", slug="hidden")
    make_product(store=store, name="Inactive", slug="inactive", is_active=False)
    client = APIClient()

    response = client.get("/api/v1/storefront/green-mart/products/")

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["results"]}
    assert ids == {str(visible.id), str(uncategorized.id)}


@pytest.mark.django_db
def test_public_discovery_searches_active_stores_and_products_without_leaking_hidden_data():
    visible_store = make_store(name="Fresh Basket", slug="fresh-basket")
    hidden_store = make_store(name="Closed Basket", slug="closed-basket")
    hidden_store.status = "suspended"
    hidden_store.save(update_fields=("status", "updated_at"))
    category = make_category(store=visible_store, name="Fruit", slug="fruit")
    visible_product = make_product(
        store=visible_store,
        category=category,
        name="Green Apple",
        slug="green-apple",
    )
    make_product(store=hidden_store, name="Hidden Apple", slug="hidden-apple")
    make_product(store=visible_store, name="Inactive Apple", slug="inactive-apple", is_active=False)
    client = APIClient()

    stores = client.get("/api/v1/storefronts/", {"q": "fresh"})
    products = client.get("/api/v1/products/search/", {"q": "apple"})

    assert stores.status_code == 200
    assert [store["slug"] for store in stores.json()["results"]] == ["fresh-basket"]
    assert products.status_code == 200
    assert [product["id"] for product in products.json()["results"]] == [str(visible_product.id)]
    assert products.json()["results"][0]["store_slug"] == "fresh-basket"

