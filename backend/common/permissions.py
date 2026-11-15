from rest_framework.permissions import BasePermission


class IsSystemAdmin(BasePermission):
    """Chỉ tài khoản role=ADMIN (quản trị viên hệ thống) mới được truy cập."""

    message = "Chỉ Quản trị viên hệ thống mới có quyền truy cập."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, "role", None) == "ADMIN")
