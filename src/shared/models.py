"""
Các model trừu tượng dùng chung, cung cấp UUID và thông tin tạo/sửa bản ghi.
"""

import uuid

from django.conf import settings
from django.db import models


class BaseAuditModel(models.Model):
    """Lớp dùng chung cho thông tin tạo/sửa; không tạo bảng riêng trong database."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created_by",
        help_text="Người tạo bản ghi",
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated_by",
        help_text="Người cập nhật bản ghi",
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class UUIDModel(BaseAuditModel):
    """Kế thừa thông tin tạo/sửa và thêm khóa chính UUID cho model nghiệp vụ."""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, help_text="Định danh duy nhất UUID"
    )

    class Meta:
        abstract = True
