import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.stores.tests.factories import make_store, make_user


@pytest.mark.django_db
def test_login_returns_revocable_token_and_assigned_stores():
    user = make_user(email="admin@example.com")
    store = make_store(name="Green Mart", slug="green-mart", admin=user)
    client = APIClient()

    response = client.post(
        "/api/v1/auth/login/",
        {"email": "ADMIN@example.com", "password": "test-password"},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["token"] == Token.objects.get(user=user).key
    assert response.json()["stores"] == [
        {"id": str(store.id), "name": store.name, "slug": store.slug}
    ]


@pytest.mark.django_db
def test_logout_revokes_token():
    user = make_user(email="admin@example.com")
    token = Token.objects.create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    response = client.post("/api/v1/auth/logout/")

    assert response.status_code == 204
    assert not Token.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_only_super_admin_can_create_staff_user():
    ordinary_user = make_user(email="ordinary@example.com")
    client = APIClient()
    client.force_authenticate(ordinary_user)

    denied = client.post(
        "/api/v1/users/",
        {"email": "new@example.com", "full_name": "New User", "password": "StrongPass!123"},
        format="json",
    )

    assert denied.status_code == 403

    super_admin = make_user(email="root@example.com", is_superuser=True)
    client.force_authenticate(super_admin)
    created = client.post(
        "/api/v1/users/",
        {"email": "new@example.com", "full_name": "New User", "password": "StrongPass!123"},
        format="json",
    )
    assert created.status_code == 201
    assert created.json()["email"] == "new@example.com"

