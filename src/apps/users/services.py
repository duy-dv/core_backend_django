"""Nghiệp vụ tài khoản: kiểm tra quyền, băm mật khẩu và quản lý JWT."""

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.utils import get_md5_hash_password

from apps.users.models import User
from shared.constants import Role
from shared.permissions import is_admin


class UserService:
    @staticmethod
    def require_admin(actor):
        if not is_admin(actor):
            raise PermissionDenied("Yêu cầu quyền quản trị.")

    @staticmethod
    def check_mutable(user, actor):
        UserService.require_admin(actor)
        # Tránh admin tự xóa tài khoản hoặc vô hiệu hóa tài khoản quản trị hệ thống.
        if user.pk == actor.pk or user.is_superuser:
            raise PermissionDenied("Không thể sửa/xóa chính mình hoặc superuser qua API này.")

    @staticmethod
    def create_user(*, data, actor=None, registration=False):
        values = dict(data)
        allowed = {"email", "password", "full_name", "phone_number", "role"}
        if set(values) - allowed:
            raise ValidationError("Trường dữ liệu không được hỗ trợ.")
        if registration:
            values["role"] = Role.STAFF
        else:
            UserService.require_admin(actor)
        password = values.pop("password")
        values["email"] = values["email"].strip().lower()
        user = User(**values)
        # Kiểm tra độ mạnh trước khi băm; tuyệt đối không lưu mật khẩu thô.
        validate_password(password, user=user)
        user.set_password(password)
        if actor:
            user.created_by = actor
            user.updated_by = actor
        try:
            with transaction.atomic():
                user.full_clean()
                user.save()
        except IntegrityError as exc:
            raise ValidationError({"email": "Email đã được sử dụng."}) from exc
        return user

    @staticmethod
    @transaction.atomic
    def update_user(*, user, actor, data):
        user = User.objects.select_for_update().get(pk=user.pk)
        UserService.check_mutable(user, actor)
        allowed = {"full_name", "phone_number", "role", "is_active", "is_locked"}
        if set(data) - allowed:
            raise ValidationError("Trường dữ liệu không được hỗ trợ.")
        for key, value in data.items():
            setattr(user, key, value)
        user.updated_by = actor
        user.full_clean()
        user.save()
        return user

    @staticmethod
    @transaction.atomic
    def delete_user(*, user, actor):
        user = User.objects.select_for_update().get(pk=user.pk)
        UserService.check_mutable(user, actor)
        user.delete()

    @staticmethod
    def issue_tokens(user):
        if not user.is_active or user.is_locked:
            raise ValidationError("Thông tin đăng nhập không hợp lệ.")
        refresh = RefreshToken.for_user(user)
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": user,
        }

    @staticmethod
    def authenticate_user(email: str, password: str) -> dict:
        # Django vẫn thực hiện băm giả nếu email không tồn tại để hạn chế dò tài khoản.
        user = authenticate(email=email.strip().lower(), password=password)
        if user is None:
            raise ValidationError("Thông tin đăng nhập không hợp lệ.")
        return UserService.issue_tokens(user)

    @staticmethod
    @transaction.atomic
    def refresh_access_token(refresh_token_str: str):
        try:
            token = RefreshToken(refresh_token_str)
            # Tuần tự hóa thao tác trên cùng token; PostgreSQL hỗ trợ khóa hàng.
            OutstandingToken.objects.select_for_update().get(jti=token["jti"])
            # Kiểm tra lại tài khoản: token còn hạn vẫn bị từ chối khi tài khoản bị khóa.
            user = User.objects.filter(pk=token["user_id"]).first()
            if not user or not user.is_active or user.is_locked:
                raise ValidationError("Refresh token không hợp lệ.")
            if token.get("hash_password") != get_md5_hash_password(user.password):
                raise ValidationError("Mật khẩu đã thay đổi; hãy đăng nhập lại.")
            serializer = TokenRefreshSerializer(data={"refresh": refresh_token_str})
            serializer.is_valid(raise_exception=True)
            return serializer.validated_data
        except (
            TokenError,
            KeyError,
            ValueError,
            OutstandingToken.DoesNotExist,
            User.DoesNotExist,
        ) as exc:
            raise ValidationError("Refresh token không hợp lệ hoặc đã hết hạn.") from exc

    @staticmethod
    @transaction.atomic
    def logout_user(refresh_token_str: str):
        try:
            token = RefreshToken(refresh_token_str)
            # Tuần tự hóa thao tác trên cùng token; PostgreSQL hỗ trợ khóa hàng.
            OutstandingToken.objects.select_for_update().get(jti=token["jti"])
            token.blacklist()
        except (TokenError, OutstandingToken.DoesNotExist) as exc:
            raise ValidationError("Refresh token không hợp lệ hoặc đã hết hạn.") from exc
