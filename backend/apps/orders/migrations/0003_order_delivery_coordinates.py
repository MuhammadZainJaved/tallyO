from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0002_customer_email_order_email_snapshot")]

    operations = [
        migrations.AddField(
            model_name="order",
            name="delivery_latitude",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="delivery_longitude",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="delivery_distance_miles",
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
    ]
