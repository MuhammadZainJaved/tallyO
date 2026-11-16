from rest_framework import serializers

from apps.reporting.models import DailyOrderReport


class DailyOrderReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyOrderReport
        fields = (
            "id", "report_date", "timezone", "status", "recipients", "order_count",
            "summary", "sent_at", "error_message", "created_at", "updated_at",
        )

