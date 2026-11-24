from rest_framework.pagination import CursorPagination

from common.responses import api_success


class TimeCursorPagination(CursorPagination):
    """
    Phân trang con trỏ theo created_at (Cursor Pagination).
    Khác Offset/Limit: bài mới chèn lên đầu không làm trùng/nhảy bài ở trang sau.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50
    cursor_query_param = "cursor"
    ordering = ("-created_at", "-id")

    def get_paginated_response(self, data, extra=None, message="Thành công"):
        payload = {"results": data, "next": self.get_next_link(), "previous": self.get_previous_link()}
        if extra:
            payload.update(extra)
        return api_success(payload, message=message)


class MessageCursorPagination(TimeCursorPagination):
    page_size = 30


def paginate(request, queryset, serialize, paginator_class=TimeCursorPagination, extra=None, message="Thành công"):
    """Tiện ích: phân trang queryset rồi gọi hàm serialize(list_obj) -> list dict."""
    paginator = paginator_class()
    page = paginator.paginate_queryset(queryset, request)
    return paginator.get_paginated_response(serialize(page), extra=extra, message=message)
