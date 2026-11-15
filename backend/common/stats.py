from datetime import datetime, time, timedelta

from django.utils import timezone


def count_per_day(queryset, field="created_at", days=14):
    """
    Đếm bản ghi theo ngày (giờ Việt Nam) trong N ngày gần nhất.
    Gom nhóm bằng Python thay vì TruncDate để không phụ thuộc bảng múi giờ của MySQL (CONVERT_TZ).
    """
    today = timezone.localdate()
    start_date = today - timedelta(days=days - 1)
    start = timezone.make_aware(datetime.combine(start_date, time.min))
    buckets = {str(start_date + timedelta(days=i)): 0 for i in range(days)}
    for value in queryset.filter(**{f"{field}__gte": start}).values_list(field, flat=True):
        key = str(timezone.localtime(value).date())
        if key in buckets:
            buckets[key] += 1
    return buckets
