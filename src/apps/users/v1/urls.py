"""
Đường dẫn xác thực và quản lý người dùng của API phiên bản 1.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.users.v1.views.auth import AuthenticationViewSet
from apps.users.v1.views.users import UserViewSetV1

router = DefaultRouter()
router.register(r"auth", AuthenticationViewSet, basename="auth-v1")
router.register(r"", UserViewSetV1, basename="user-v1")

urlpatterns = [
    path("", include(router.urls)),
]
