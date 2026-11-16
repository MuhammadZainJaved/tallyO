from django.conf import settings
from django.core.validators import RegexValidator
from django.core.validators import MinValueValidator
from django.core.validators import MaxValueValidator
from django.db import models
from decimal import Decimal

from apps.core.models import TimestampedUUIDModel
from apps.stores.validators import validate_timezone

hex_color_validator = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message="Use a six-digit hexadecimal color such as #1F2937.",
)


class StoreQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status=Store.Status.ACTIVE)

    def visible_to(self, user):
        if not user.is_authenticated:
            return self.none()
        if user.is_superuser:
            return self
        return self.filter(memberships__user=user, memberships__is_active=True).distinct()


class Store(TimestampedUUIDModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=80, unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    timezone = models.CharField(max_length=64, default="UTC", validators=[validate_timezone])
    currency = models.CharField(max_length=3, default="PKR")
    delivery_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    location_address = models.CharField(max_length=500, blank=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("-90")), MaxValueValidator(Decimal("90"))],
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("-180")), MaxValueValidator(Decimal("180"))],
    )
    delivery_radius_miles = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("0.10")), MaxValueValidator(Decimal("100.00"))],
    )
    delivery_radius_enabled = models.BooleanField(default=False)

    objects = StoreQuerySet.as_manager()

    class Meta:
        ordering = ("name",)
        indexes = [models.Index(fields=("status",), name="store_status_idx")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(delivery_fee__gte=0),
                name="store_delivery_fee_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(delivery_radius_miles__gte=Decimal("0.10")),
                name="store_delivery_radius_positive",
            ),
            models.CheckConstraint(
                condition=(models.Q(latitude__isnull=True, longitude__isnull=True) | models.Q(latitude__isnull=False, longitude__isnull=False)),
                name="store_location_coordinates_pair",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(delivery_radius_enabled=False)
                    | models.Q(latitude__isnull=False, longitude__isnull=False)
                ),
                name="store_radius_requires_location",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class StoreBranding(TimestampedUUIDModel):
    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name="branding")
    logo_url = models.URLField(blank=True)
    banner_url = models.URLField(blank=True)
    primary_color = models.CharField(max_length=7, default="#1F2937", validators=[hex_color_validator])
    secondary_color = models.CharField(max_length=7, default="#0F172A", validators=[hex_color_validator])
    footer_text = models.CharField(max_length=500, blank=True)

    def __str__(self) -> str:
        return f"Branding for {self.store}"


class StoreMembership(TimestampedUUIDModel):
    class Role(models.TextChoices):
        ADMIN = "admin", "Store admin"

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="store_memberships")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.ADMIN)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("store", "user"), name="store_membership_unique")
        ]
        indexes = [
            models.Index(fields=("user", "is_active"), name="membership_user_active_idx"),
            models.Index(fields=("store", "is_active"), name="membership_store_active_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.store} ({self.role})"

