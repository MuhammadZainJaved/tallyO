from decimal import Decimal

from django.db import models

from apps.core.models import TimestampedUUIDModel


class DailyOrderReport(TimestampedUUIDModel):
    class Status(models.TextChoices):
        PROCESSING = "processing", "Processing"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    report_date = models.DateField()
    timezone = models.CharField(max_length=64)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PROCESSING)
    recipients = models.JSONField(default=list)
    order_count = models.PositiveIntegerField(default=0)
    summary = models.JSONField(default=list)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ("-report_date", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("report_date", "timezone"),
                name="daily_report_date_timezone_unique",
            )
        ]

    def __str__(self) -> str:
        return f"Daily orders {self.report_date} ({self.timezone})"

