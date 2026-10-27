"""Quản lý tài khoản bằng quyền admin và xem thông tin cá nhân."""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.models import User
from apps.users.services import UserService
from apps.users.v1.serializers.users import (
    UserCreateSerializer,
    UserMinimalSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from shared.mixins import BulkDeleteMixin, MinimalMixin
from shared.permissions import IsAdmin
from shared.serializers import BulkDeleteSerializer


@extend_schema_view(
    minimal=extend_schema(responses={200: UserMinimalSerializer(many=True)}),
    create=extend_schema(responses={201: UserSerializer}),
    update=extend_schema(responses={200: UserSerializer}),
    partial_update=extend_schema(responses={200: UserSerializer}),
)
class UserViewSetV1(MinimalMixin, BulkDeleteMixin, viewsets.ModelViewSet):
    queryset = User.objects.order_by("-created_at", "id")
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["role", "is_active", "is_locked"]
    search_fields = ["email", "full_name"]
    ordering_fields = ["created_at", "email", "full_name"]

    def get_serializer_class(self):
        if self.action == "minimal":
            return UserMinimalSerializer
        if self.action == "delete_many":
            return BulkDeleteSerializer
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        # Người dùng thường chỉ được xem thông tin của chính mình.
        if self.action == "me":
            return [IsAuthenticated()]
        return [IsAdmin()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.create_user(data=serializer.validated_data, actor=request.user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        # PATCH chỉ sửa trường được gửi; PUT yêu cầu các trường bắt buộc.
        partial = kwargs.pop("partial", False)
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = UserService.update_user(
            user=user, actor=request.user, data=serializer.validated_data
        )
        return Response(UserSerializer(user).data)

    def perform_destroy(self, instance):
        UserService.delete_user(user=instance, actor=self.request.user)

    def check_delete_permission(self, obj):
        # Cùng quy tắc với xóa đơn: không xóa chính mình hoặc superuser.
        super().check_delete_permission(obj)
        UserService.check_mutable(obj, self.request.user)

    @action(detail=False, methods=["GET"])
    def me(self, request):
        """Xem thông tin của tài khoản đang đăng nhập."""
        return Response(UserSerializer(request.user).data)
