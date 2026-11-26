from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView

from common.pagination import paginate
from common.responses import api_success

from . import services


class NotificationListView(APIView):
    """UC-26: danh sách thông báo (cursor) kèm số chưa đọc."""

    def get(self, request):
        extra = {"unread_count": services.unread_count(request.user.id)}
        return paginate(request, services.list_queryset(request.user), services.serialize_many, extra=extra)


class UnreadCountView(APIView):
    def get(self, request):
        return api_success({"unread_count": services.unread_count(request.user.id)})


class MarkReadView(APIView):
    @extend_schema(request=None)
    def post(self, request, notification_id):
        services.mark_read(request.user, notification_id)
        return api_success({"unread_count": services.unread_count(request.user.id)})


class MarkAllReadView(APIView):
    @extend_schema(request=None)
    def post(self, request):
        services.mark_all_read(request.user)
        return api_success({"unread_count": 0}, "Đã đánh dấu tất cả là đã đọc")
