from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from apps.core.models import TimestampedUUIDModel
from apps.stores.models import Store


class Category(TimestampedUUIDModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120)
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("display_order", "name")
        constraints = [
            models.UniqueConstraint(fields=("store", "slug"), name="category_store_slug_unique")
        ]
        indexes = [
            models.Index(
                fields=("store", "is_active", "display_order"),
                name="category_store_active_idx",
            )
        ]

    def __str__(self) -> str:
        return f"{self.store}: {self.name}"


class Product(TimestampedUUIDModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="products",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=80, blank=True)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    image_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    track_inventory = models.BooleanField(default=False)
    stock_quantity = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(fields=("store", "slug"), name="product_store_slug_unique"),
            models.UniqueConstraint(
                fields=("store", "sku"),
                condition=~Q(sku=""),
                name="product_store_sku_unique",
            ),
            models.CheckConstraint(condition=Q(price__gte=0), name="product_price_nonnegative"),
        ]
        indexes = [
            models.Index(fields=("store", "is_active"), name="product_store_active_idx"),
            models.Index(
                fields=("store", "category", "is_active"),
                name="product_store_cat_active_idx",
            ),
        ]

    def clean(self):
        super().clean()
        if self.category_id and self.category.store_id != self.store_id:
            raise ValidationError({"category": "Category must belong to the same store."})

    @property
    def is_available(self) -> bool:
        return self.is_active and (not self.track_inventory or self.stock_quantity > 0)

    def __str__(self) -> str:
        return f"{self.store}: {self.name}"

