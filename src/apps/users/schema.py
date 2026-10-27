"""Báo cho Swagger rằng lớp xác thực riêng vẫn sử dụng Bearer JWT."""

from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme


class ActiveJWTScheme(SimpleJWTScheme):
    target_class = "apps.users.authentication.ActiveJWTAuthentication"
