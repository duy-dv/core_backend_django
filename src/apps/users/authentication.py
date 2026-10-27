"""Chặn tài khoản bị khóa khi đăng nhập bằng mật khẩu hoặc gọi API bằng JWT."""

from django.contrib.auth.backends import ModelBackend
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class ActiveUserBackend(ModelBackend):
    def user_can_authenticate(self, user):
        return super().user_can_authenticate(user) and not user.is_locked


class ActiveJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if user.is_locked:
            raise AuthenticationFailed("Tài khoản không thể đăng nhập.")
        return user
