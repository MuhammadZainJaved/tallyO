from dataclasses import dataclass
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.stores.models import Store, StoreBranding, StoreMembership

User = get_user_model()


@dataclass(frozen=True, slots=True)
class CreateStoreCommand:
    name: str
    slug: str
    timezone: str
    currency: str = "PKR"
    delivery_fee: Decimal = Decimal("0.00")
    location_address: str = ""
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    delivery_radius_miles: Decimal = Decimal("1.00")
    delivery_radius_enabled: bool = False
    admin_email: str | None = None


@transaction.atomic
def create_store(*, command: CreateStoreCommand, actor) -> Store:
    if not actor.is_authenticated or not actor.is_superuser:
        raise PermissionDenied("Only a super admin can create a store.")

    store = Store(
        name=command.name,
        slug=command.slug,
        timezone=command.timezone,
        currency=command.currency.upper(),
        delivery_fee=command.delivery_fee,
        location_address=command.location_address,
        latitude=command.latitude,
        longitude=command.longitude,
        delivery_radius_miles=command.delivery_radius_miles,
        delivery_radius_enabled=command.delivery_radius_enabled,
    )
    store.full_clean()
    store.save()
    StoreBranding.objects.create(store=store)

    if command.admin_email:
        try:
            admin = User.objects.get(email__iexact=command.admin_email.strip())
        except User.DoesNotExist as exc:
            raise ValidationError({"admin_email": "The store admin account does not exist."}) from exc
        StoreMembership.objects.create(store=store, user=admin, role=StoreMembership.Role.ADMIN)

    return store

