import uuid
from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("stores", "0002_store_commerce_fields")]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("store", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="categories", to="stores.store")),
            ],
            options={
                "ordering": ("display_order", "name"),
                "indexes": [models.Index(fields=["store", "is_active", "display_order"], name="category_store_active_idx")],
                "constraints": [models.UniqueConstraint(fields=("store", "slug"), name="category_store_slug_unique")],
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=180)),
                ("slug", models.SlugField(max_length=180)),
                ("description", models.TextField(blank=True)),
                ("sku", models.CharField(blank=True, max_length=80)),
                ("price", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
                ("image_url", models.URLField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("track_inventory", models.BooleanField(default=False)),
                ("stock_quantity", models.PositiveIntegerField(default=0)),
                ("category", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="products", to="catalog.category")),
                ("store", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="products", to="stores.store")),
            ],
            options={
                "ordering": ("name",),
                "indexes": [
                    models.Index(fields=["store", "is_active"], name="product_store_active_idx"),
                    models.Index(fields=["store", "category", "is_active"], name="product_store_cat_active_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=("store", "slug"), name="product_store_slug_unique"),
                    models.UniqueConstraint(condition=models.Q(("sku", ""), _negated=True), fields=("store", "sku"), name="product_store_sku_unique"),
                    models.CheckConstraint(condition=models.Q(("price__gte", 0)), name="product_price_nonnegative"),
                ],
            },
        ),
    ]

