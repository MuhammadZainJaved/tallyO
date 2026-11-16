from django.contrib import admin

from apps.reporting.models import DailyOrderReport


@admin.register(DailyOrderReport)
class DailyOrderReportAdmin(admin.ModelAdmin):
    list_display = ("report_date", "timezone", "status", "order_count", "sent_at")
    list_filter = ("status", "timezone")
    readonly_fields = (
        "report_date", "timezone", "status", "recipients", "order_count", "summary",
        "sent_at", "error_message", "created_at", "updated_at",
    )

