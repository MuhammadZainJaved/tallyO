from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.core.permissions import IsSuperAdmin
from apps.reporting.api.serializers import DailyOrderReportSerializer
from apps.reporting.models import DailyOrderReport


class DailyOrderReportViewSet(ReadOnlyModelViewSet):
    permission_classes = (IsSuperAdmin,)
    serializer_class = DailyOrderReportSerializer
    queryset = DailyOrderReport.objects.all()

