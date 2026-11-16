# Generated for Django 5.2.
import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators

import apps.stores.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Store",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=150)),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("status", models.CharField(choices=[("active", "Active"), ("suspended", "Suspended")], default="active", max_length=16)),
                ("timezone", models.CharField(default="UTC", max_length=64, validators=[apps.stores.validators.validate_timezone])),
            ],
            options={
                "ordering": ("name",),
                "indexes": [models.Index(fields=["status"], name="store_status_idx")],
            },
        ),
        migrations.CreateModel(
            name="StoreBranding",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("logo_url", models.URLField(blank=True)),
                ("banner_url", models.URLField(blank=True)),
                ("primary_color", models.CharField(default="#1F2937", max_length=7, validators=[django.core.validators.RegexValidator(message="Use a six-digit hexadecimal color such as #1F2937.", regex="^#[0-9A-Fa-f]{6}$")])),
                ("secondary_color", models.CharField(default="#FFFFFF", max_length=7, validators=[django.core.validators.RegexValidator(message="Use a six-digit hexadecimal color such as #1F2937.", regex="^#[0-9A-Fa-f]{6}$")])),
                ("footer_text", models.CharField(blank=True, max_length=500)),
                ("store", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="branding", to="stores.store")),
            ],
        ),
        migrations.CreateModel(
            name="StoreMembership",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("role", models.CharField(choices=[("admin", "Store admin")], default="admin", max_length=16)),
                ("is_active", models.BooleanField(default=True)),
                ("store", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="stores.store")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="store_memberships", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["user", "is_active"], name="membership_user_active_idx"),
                    models.Index(fields=["store", "is_active"], name="membership_store_active_idx"),
                ],
                "constraints": [models.UniqueConstraint(fields=("store", "user"), name="store_membership_unique")],
            },
        ),
    ]

