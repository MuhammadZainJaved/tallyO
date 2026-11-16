import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction


User = get_user_model()


@pytest.mark.django_db
def test_user_email_is_normalized_to_lowercase():
    user = User.objects.create_user(
        email="Owner@Example.COM",
        password="a-secure-password",
        full_name="Store Owner",
    )

    assert user.email == "owner@example.com"


@pytest.mark.django_db
def test_email_is_unique_case_insensitively():
    User.objects.create_user(email="owner@example.com", password="password", full_name="Owner")

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(email="OWNER@example.com", password="password", full_name="Other")


@pytest.mark.django_db
def test_superuser_has_required_flags():
    user = User.objects.create_superuser(
        email="root@example.com",
        password="a-secure-password",
        full_name="Root Admin",
    )

    assert user.is_staff is True
    assert user.is_superuser is True

