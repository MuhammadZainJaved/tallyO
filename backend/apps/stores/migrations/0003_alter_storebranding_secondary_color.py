from django.db import migrations, models

import apps.stores.models


class Migration(migrations.Migration):
    dependencies = [("stores", "0002_store_commerce_fields")]

    operations = [
        migrations.AlterField(
            model_name="storebranding",
            name="secondary_color",
            field=models.CharField(
                default="#0F172A",
                max_length=7,
                validators=[apps.stores.models.hex_color_validator],
            ),
        ),
    ]
