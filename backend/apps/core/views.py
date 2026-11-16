from django.db import connection
from django.http import JsonResponse
from django.views import View


class HealthCheckView(View):
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse({"status": "ok"})

