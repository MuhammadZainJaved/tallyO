import pytest
from decimal import Decimal
from rest_framework.test import APIClient

from apps.stores.tests.factories import make_store, make_user


@pytest.mark.django_db
def test_store_admin_only_lists_assigned_stores():
    admin = make_user(email="admin@example.com")
    own_store = make_store(name="Own Store", slug="own-store", admin=admin)
    make_store(name="Other Store", slug="other-store")
    client = APIClient()
    client.force_authenticate(admin)

    response = client.get("/api/v1/stores/")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["results"]] == [str(own_store.id)]


@pytest.mark.django_db
def test_store_admin_gets_404_for_another_store():
    admin = make_user(email="admin@example.com")
    make_store(name="Own Store", slug="own-store", admin=admin)
    other_store = make_store(name="Other Store", slug="other-store")
    client = APIClient()
    client.force_authenticate(admin)

    response = client.get(f"/api/v1/stores/{other_store.id}/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_store_admin_cannot_create_store():
    admin = make_user(email="admin@example.com")
    client = APIClient()
    client.force_authenticate(admin)

    response = client.post(
        "/api/v1/stores/",
        {"name": "Forbidden", "slug": "forbidden", "timezone": "UTC"},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_super_admin_can_list_every_store():
    super_admin = make_user(email="root@example.com", is_superuser=True)
    make_store(name="Store One", slug="store-one")
    make_store(name="Store Two", slug="store-two")
    client = APIClient()
    client.force_authenticate(super_admin)

    response = client.get("/api/v1/stores/")

    assert response.status_code == 200
    assert len(response.json()["results"]) == 2


@pytest.mark.django_db
def test_store_admin_can_update_own_branding_atomically():
    admin = make_user(email="admin@example.com")
    store = make_store(name="Own Store", slug="own-store", admin=admin)
    client = APIClient()
    client.force_authenticate(admin)

    response = client.patch(
        f"/api/v1/stores/{store.id}/",
        {"branding": {"primary_color": "#112233", "footer_text": "Thank you"}},
        format="json",
    )

    assert response.status_code == 200
    store.branding.refresh_from_db()
    assert store.branding.primary_color == "#112233"
    assert store.branding.footer_text == "Thank you"


@pytest.mark.django_db
def test_store_admin_can_configure_delivery_marker_and_radius():
    admin = make_user(email="admin@example.com")
    store = make_store(name="Own Store", slug="own-store", admin=admin)
    client = APIClient()
    client.force_authenticate(admin)

    response = client.patch(
        f"/api/v1/stores/{store.id}/",
        {
            "location_address": "Model Town, Lahore",
            "latitude": "31.520400",
            "longitude": "74.358700",
            "delivery_radius_miles": "1.50",
            "delivery_radius_enabled": True,
        },
        format="json",
    )

    assert response.status_code == 200
    store.refresh_from_db()
    assert store.delivery_radius_enabled is True
    assert store.delivery_radius_miles == Decimal("1.50")


@pytest.mark.django_db
def test_delivery_radius_cannot_be_enabled_without_store_marker():
    admin = make_user(email="admin@example.com")
    store = make_store(name="Own Store", slug="own-store", admin=admin)
    client = APIClient()
    client.force_authenticate(admin)

    response = client.patch(
        f"/api/v1/stores/{store.id}/",
        {"delivery_radius_enabled": True},
        format="json",
    )

    assert response.status_code == 400

