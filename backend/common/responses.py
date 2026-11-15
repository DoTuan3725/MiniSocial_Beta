"""Định dạng phản hồi thống nhất: { success, message, data } hoặc { success: false, message, errors }."""

from rest_framework import status
from rest_framework.response import Response


def api_success(data=None, message="Thành công", status_code=status.HTTP_200_OK):
    return Response({"success": True, "message": message, "data": data if data is not None else {}}, status=status_code)


def api_error(message="Đã có lỗi xảy ra", errors=None, status_code=status.HTTP_400_BAD_REQUEST, code=None):
    payload = {"success": False, "message": message, "errors": errors if errors is not None else {}}
    if code:
        payload["code"] = code
    return Response(payload, status=status_code)
