from decimal import Decimal

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("stores", "0003_alter_storebranding_secondary_color")]

    operations = [
        migrations.AddField(
            model_name="store",
            name="location_address",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="store",
            name="latitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(Decimal("-90")),
                    django.core.validators.MaxValueValidator(Decimal("90")),
                ],
            ),
        ),
        migrations.AddField(
            model_name="store",
            name="longitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(Decimal("-180")),
                    django.core.validators.MaxValueValidator(Decimal("180")),
                ],
            ),
        ),
        migrations.AddField(
            model_name="store",
            name="delivery_radius_miles",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("1.00"),
                max_digits=5,
                validators=[
                    django.core.validators.MinValueValidator(Decimal("0.10")),
                    django.core.validators.MaxValueValidator(Decimal("100.00")),
                ],
            ),
        ),
        migrations.AddField(
            model_name="store",
            name="delivery_radius_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddConstraint(
            model_name="store",
            constraint=models.CheckConstraint(
                condition=models.Q(("delivery_radius_miles__gte", Decimal("0.10"))),
                name="store_delivery_radius_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="store",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(("latitude__isnull", True), ("longitude__isnull", True))
                    | models.Q(("latitude__isnull", False), ("longitude__isnull", False))
                ),
                name="store_location_coordinates_pair",
            ),
        ),
        migrations.AddConstraint(
            model_name="store",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(("delivery_radius_enabled", False))
                    | models.Q(("latitude__isnull", False), ("longitude__isnull", False))
                ),
                name="store_radius_requires_location",
            ),
        ),
    ]
