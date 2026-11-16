import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.stores.models import Store, StoreBranding, StoreMembership
from apps.stores.services import CreateStoreCommand, create_store
from apps.stores.tests.factories import make_user


@pytest.mark.django_db
def test_super_admin_can_create_store_and_assign_existing_admin():
    super_admin = make_user(email="root@example.com", is_superuser=True)
    store_admin = make_user(email="admin@example.com")

    store = create_store(
        command=CreateStoreCommand(
            name="Green Mart",
            slug="green-mart",
            timezone="Asia/Karachi",
            admin_email="ADMIN@example.com",
        ),
        actor=super_admin,
    )

    assert StoreBranding.objects.filter(store=store).exists()
    assert StoreMembership.objects.filter(store=store, user=store_admin, is_active=True).exists()


@pytest.mark.django_db
def test_store_creation_rolls_back_when_admin_does_not_exist():
    super_admin = make_user(email="root@example.com", is_superuser=True)

    with pytest.raises(ValidationError):
        create_store(
            command=CreateStoreCommand(
                name="Green Mart",
                slug="green-mart",
                timezone="Asia/Karachi",
                admin_email="missing@example.com",
            ),
            actor=super_admin,
        )

    assert not Store.objects.filter(slug="green-mart").exists()


@pytest.mark.django_db
def test_regular_user_cannot_create_store():
    user = make_user(email="user@example.com")

    with pytest.raises(PermissionDenied):
        create_store(
            command=CreateStoreCommand(name="Store", slug="store", timezone="UTC"),
            actor=user,
        )

