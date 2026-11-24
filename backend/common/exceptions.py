"""
Chuẩn hóa lỗi REST về cùng một định dạng.
Lỗi 500 không bị nuốt: Django/Sentry SDK vẫn bắt và gửi về Sentry -> Discord.
"""

import logging

from rest_framework import status
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Lỗi nghiệp vụ ném ra từ tầng Service, được chuyển thành HTTP 4xx."""

    def __init__(self, message, status_code=status.HTTP_400_BAD_REQUEST, code=None, errors=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.errors = errors or {}


class NotFound(ServiceError):
    def __init__(self, message="Không tìm thấy dữ liệu"):
        super().__init__(message, status.HTTP_404_NOT_FOUND, "NOT_FOUND")


class PermissionDenied(ServiceError):
    def __init__(self, message="Bạn không có quyền thực hiện thao tác này"):
        super().__init__(message, status.HTTP_403_FORBIDDEN, "FORBIDDEN")


def api_exception_handler(exc, context):
    from rest_framework.views import exception_handler

    from common.responses import api_error

    if isinstance(exc, ServiceError):
        return api_error(exc.message, exc.errors, exc.status_code, exc.code)

    response = exception_handler(exc, context)
    if response is None:
        return None  # để Django trả 500 và Sentry ghi nhận

    if isinstance(exc, ValidationError):
        message = "Dữ liệu không hợp lệ"
        errors = response.data
    else:
        detail = response.data.get("detail") if isinstance(response.data, dict) else None
        message = str(detail) if detail else "Yêu cầu không thành công"
        errors = {} if detail else response.data
    response.data = {"success": False, "message": message, "errors": errors}
    if getattr(exc, "default_code", None):
        response.data["code"] = str(getattr(exc, "default_code")).upper()
    if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        response.data["message"] = "Bạn thao tác quá nhanh, vui lòng thử lại sau."
    return response
