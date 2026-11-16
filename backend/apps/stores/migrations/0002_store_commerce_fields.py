from decimal import Decimal

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("stores", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="store",
            name="currency",
            field=models.CharField(default="PKR", max_length=3),
        ),
        migrations.AddField(
            model_name="store",
            name="delivery_fee",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
            ),
        ),
        migrations.AddConstraint(
            model_name="store",
            constraint=models.CheckConstraint(
                condition=models.Q(("delivery_fee__gte", 0)),
                name="store_delivery_fee_nonnegative",
            ),
        ),
    ]

