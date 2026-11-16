from zoneinfo import ZoneInfo

import pytest
from django.conf import settings
from django.core import mail
from django.utils import timezone

from apps.catalog.tests.factories import make_product
from apps.orders.tests.factories import make_order
from apps.reporting.models import DailyOrderReport
from apps.reporting.tasks import send_daily_order_report
from apps.stores.tests.factories import make_store, make_user


@pytest.mark.django_db
def test_daily_report_is_emailed_to_active_super_admins_once():
    make_user(email="root@example.com", is_superuser=True)
    make_user(email="ordinary@example.com")
    store = make_store(name="Green Mart", slug="green-mart")
    make_order(store=store, product=make_product(store=store))
    report_date = timezone.now().astimezone(ZoneInfo(settings.REPORT_TIMEZONE)).date()

    first = send_daily_order_report.apply(args=[report_date.isoformat()]).get()
    second = send_daily_order_report.apply(args=[report_date.isoformat()]).get()

    assert first["status"] == "sent"
    assert second["status"] == "already_sent"
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["root@example.com"]
    assert mail.outbox[0].attachments[0][0].startswith("orders-")
    report = DailyOrderReport.objects.get(report_date=report_date)
    assert report.status == DailyOrderReport.Status.SENT
    assert report.order_count == 1

