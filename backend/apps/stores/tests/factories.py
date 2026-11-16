from django.contrib.auth import get_user_model

from apps.stores.models import Store, StoreBranding, StoreMembership


User = get_user_model()


def make_user(*, email: str, is_superuser: bool = False):
    return User.objects.create_user(
        email=email,
        password="test-password",
        full_name="Test User",
        is_staff=is_superuser,
        is_superuser=is_superuser,
    )


def make_store(*, name: str, slug: str, admin=None):
    store = Store.objects.create(name=name, slug=slug, timezone="Asia/Karachi")
    StoreBranding.objects.create(store=store)
    if admin is not None:
        StoreMembership.objects.create(store=store, user=admin)
    return store

