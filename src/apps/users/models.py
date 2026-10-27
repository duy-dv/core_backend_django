"""
Mô hình người dùng đăng nhập bằng email và bộ quản lý tạo tài khoản.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models.functions import Lower

from shared.constants import Role
from shared.models import UUIDModel


class UserManager(BaseUserManager):
    """Tạo tài khoản thường và superuser; luôn băm mật khẩu trước khi lưu."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email là bắt buộc.")
        if not password:
            raise ValueError("Mật khẩu là bắt buộc.")

        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.ADMIN)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)

        if extra_fields.get("role") != Role.ADMIN:
            raise ValueError("Superuser phải có role=Role.ADMIN.")
        if extra_fields.get("is_staff") is not True or extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser phải có is_staff=True và is_superuser=True.")

        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, UUIDModel):
    """
    Người dùng có ID dạng UUID, thông tin tạo/sửa và vai trò truy cập.
    """

    email = models.EmailField(unique=True, db_index=True, verbose_name="Địa chỉ Email")
    phone_number = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Số điện thoại"
    )
    full_name = models.CharField(max_length=255, verbose_name="Họ và tên")
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")
    role = models.CharField(
        max_length=50, choices=Role.choices, default=Role.STAFF, verbose_name="Vai trò"
    )
    is_locked = models.BooleanField(default=False, verbose_name="Đã khóa")

    # Giữ is_staff để tương thích User của Django; phân quyền API dùng role/is_superuser.
    is_staff = models.BooleanField(default=False, verbose_name="Nhân viên ban quản trị")

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name = "Người dùng"
        verbose_name_plural = "Danh sách người dùng"
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(Lower("email"), name="users_email_ci_unique")]

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.email})"
