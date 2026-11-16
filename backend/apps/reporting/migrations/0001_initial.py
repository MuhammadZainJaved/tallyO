import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DailyOrderReport",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("report_date", models.DateField()),
                ("timezone", models.CharField(max_length=64)),
                ("status", models.CharField(choices=[("processing", "Processing"), ("sent", "Sent"), ("failed", "Failed")], default="processing", max_length=16)),
                ("recipients", models.JSONField(default=list)),
                ("order_count", models.PositiveIntegerField(default=0)),
                ("summary", models.JSONField(default=list)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True)),
            ],
            options={
                "ordering": ("-report_date", "-created_at"),
                "constraints": [models.UniqueConstraint(fields=("report_date", "timezone"), name="daily_report_date_timezone_unique")],
            },
        ),
    ]

