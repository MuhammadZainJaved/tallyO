import csv
import io
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.db.models import Count, Sum
from django.utils import timezone

from apps.orders.models import Order
from apps.reporting.models import DailyOrderReport


User = get_user_model()


def _date_window(report_date: date, timezone_name: str):
    zone = ZoneInfo(timezone_name)
    start = datetime.combine(report_date, time.min, tzinfo=zone)
    end = start + timedelta(days=1)
    return start, end


def _csv_content(orders) -> str:
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(
        ["order_id", "store", "status", "phone", "currency", "subtotal", "delivery_fee", "total", "created_at"]
    )
    for order in orders:
        writer.writerow(
            [
                str(order.id),
                order.store.name,
                order.status,
                order.phone_snapshot,
                order.currency,
                order.subtotal,
                order.delivery_fee,
                order.total,
                order.created_at.isoformat(),
            ]
        )
    return stream.getvalue()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_daily_order_report(self, report_date: str | None = None):
    timezone_name = settings.REPORT_TIMEZONE
    target_date = (
        date.fromisoformat(report_date)
        if report_date
        else datetime.now(ZoneInfo(timezone_name)).date() - timedelta(days=1)
    )
    report, _ = DailyOrderReport.objects.get_or_create(
        report_date=target_date,
        timezone=timezone_name,
    )
    if report.status == DailyOrderReport.Status.SENT:
        return {"status": "already_sent", "report_id": str(report.id)}

    recipients = list(
        User.objects.filter(is_superuser=True, is_active=True)
        .exclude(email="")
        .values_list("email", flat=True)
    )
    start, end = _date_window(target_date, timezone_name)
    orders = list(
        Order.objects.filter(created_at__gte=start, created_at__lt=end)
        .select_related("store")
        .order_by("store__name", "created_at")
    )
    aggregates = list(
        Order.objects.filter(created_at__gte=start, created_at__lt=end)
        .values("store__name", "currency")
        .annotate(order_count=Count("id"), total=Sum("total"))
        .order_by("store__name", "currency")
    )
    summary = [
        {
            "store": row["store__name"],
            "currency": row["currency"],
            "order_count": row["order_count"],
            "total": str(row["total"] or Decimal("0.00")),
        }
        for row in aggregates
    ]

    report.status = DailyOrderReport.Status.PROCESSING
    report.recipients = recipients
    report.order_count = len(orders)
    report.summary = summary
    report.error_message = ""
    report.save(
        update_fields=("status", "recipients", "order_count", "summary", "error_message", "updated_at")
    )
    if not recipients:
        report.status = DailyOrderReport.Status.FAILED
        report.error_message = "No active super-admin email recipients are configured."
        report.save(update_fields=("status", "error_message", "updated_at"))
        return {"status": "no_recipients", "report_id": str(report.id)}

    lines = [
        f"Daily order report for {target_date.isoformat()} ({timezone_name})",
        f"Orders: {len(orders)}",
        "",
    ]
    lines.extend(
        f"{row['store']}: {row['order_count']} orders, {row['currency']} {row['total']}"
        for row in summary
    )
    if not summary:
        lines.append("No orders were placed during this reporting day.")

    email = EmailMessage(
        subject=f"tallyO daily orders — {target_date.isoformat()}",
        body="\n".join(lines),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    email.attach(
        f"orders-{target_date.isoformat()}.csv",
        _csv_content(orders),
        "text/csv",
    )
    try:
        email.send(fail_silently=False)
    except Exception as exc:
        report.status = DailyOrderReport.Status.FAILED
        report.error_message = str(exc)[:2000]
        report.save(update_fields=("status", "error_message", "updated_at"))
        raise

    report.status = DailyOrderReport.Status.SENT
    report.sent_at = timezone.now()
    report.save(update_fields=("status", "sent_at", "updated_at"))
    return {"status": "sent", "report_id": str(report.id), "orders": len(orders)}

