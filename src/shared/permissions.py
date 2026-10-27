"""Các quyền cơ bản dùng chung giữa các ứng dụng."""

from rest_framework.permissions import BasePermission

from shared.constants import Role


def is_admin(user):
    """Kiểm tra quyền quản trị API theo role hoặc cờ superuser."""
    return bool(
        user
        and user.is_authenticated
        and user.is_active
        and not user.is_locked
        and (user.is_superuser or user.role == Role.ADMIN)
    )


class IsAdmin(BasePermission):
    message = "Yêu cầu quyền quản trị viên."

    def has_permission(self, request, view):
        return is_admin(request.user)
