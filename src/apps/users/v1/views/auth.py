"""Đăng ký, đăng nhập, làm mới token và đăng xuất."""

from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.users.services import UserService
from apps.users.v1.serializers.auth import (
    LoginResponseSerializer,
    LoginSerializer,
    RefreshTokenSerializer,
    TokenPairSerializer,
)
from apps.users.v1.serializers.users import RegistrationSerializer, UserSerializer


class AuthenticationViewSet(viewsets.GenericViewSet):
    serializer_class = LoginSerializer
    authentication_classes = []
    permission_classes = [AllowAny]
    # Hạn chế số lần thử đăng nhập/đăng ký liên tục từ cùng một IP.
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    @extend_schema(request=RegistrationSerializer, responses={201: UserSerializer})
    @action(detail=False, methods=["POST"], serializer_class=RegistrationSerializer)
    def register(self, request):
        """Đăng ký tài khoản thường, không được tự chọn quyền admin."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.create_user(data=serializer.validated_data, registration=True)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=LoginSerializer, responses={200: LoginResponseSerializer})
    @action(detail=False, methods=["POST"])
    def login(self, request):
        """Kiểm tra email/mật khẩu và cấp cặp access/refresh token."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = UserService.authenticate_user(**serializer.validated_data)
        # Chuyển đối tượng User thành JSON ngay tại tầng API.
        data["user"] = UserSerializer(data["user"]).data
        return Response(data)

    @extend_schema(request=RefreshTokenSerializer, responses={200: TokenPairSerializer})
    @action(
        detail=False, methods=["POST"], url_path="refresh", serializer_class=RefreshTokenSerializer
    )
    def refresh_token(self, request):
        """Đổi refresh token hiện tại lấy cặp token mới."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(UserService.refresh_access_token(serializer.validated_data["refresh"]))

    @extend_schema(request=RefreshTokenSerializer, responses={204: None})
    @action(detail=False, methods=["POST"], serializer_class=RefreshTokenSerializer)
    def logout(self, request):
        """Vô hiệu hóa refresh token của phiên đăng nhập hiện tại."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        UserService.logout_user(serializer.validated_data["refresh"])
        return Response(status=status.HTTP_204_NO_CONTENT)
