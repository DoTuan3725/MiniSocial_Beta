"""Health check: 200 nếu MySQL + Redis sống, 503 nếu rớt kết nối (được ping định kỳ 60s)."""

from django.db import connection
from django.http import JsonResponse

from common.redis_client import get_redis


def health_check(request):
    checks = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"error: {exc.__class__.__name__}"
    try:
        get_redis().ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"error: {exc.__class__.__name__}"
    healthy = all(v == "ok" for v in checks.values())
    return JsonResponse(
        {"status": "healthy" if healthy else "unhealthy", "checks": checks}, status=200 if healthy else 503
    )
