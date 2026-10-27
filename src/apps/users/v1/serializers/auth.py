"""Khai báo dữ liệu đăng nhập và định dạng JWT trả về."""

from rest_framework import serializers

from apps.users.v1.serializers.users import UserSerializer


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField(max_length=4096)


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)


class LoginResponseSerializer(TokenPairSerializer):
    user = UserSerializer(read_only=True)
