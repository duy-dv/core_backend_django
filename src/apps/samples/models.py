"""
Model mẫu để tham khảo khi tạo bảng dữ liệu cho dự án mới.
"""

from django.conf import settings
from django.db import models

from shared.constants import CommonStatus, Priority
from shared.models import UUIDModel


class SampleItem(UUIDModel):
    """
    Ví dụ một bảng dữ liệu nghiệp vụ có người sở hữu.
    Tự động có id dạng UUID và các trường created_at, updated_at, created_by, updated_by.
    """

    title = models.CharField(max_length=255, db_index=True, verbose_name="Tiêu đề")
    description = models.TextField(blank=True, verbose_name="Mô tả chi tiết")
    status = models.CharField(
        max_length=20,
        choices=CommonStatus.choices,
        default=CommonStatus.ACTIVE,
        db_index=True,
        verbose_name="Trạng thái",
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name="Mức độ ưu tiên",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sample_items",
        verbose_name="Người phụ trách / Sở hữu",
    )
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Dữ liệu mở rộng (JSON)")

    class Meta:
        verbose_name = "Mục mẫu"
        verbose_name_plural = "Danh sách mục mẫu"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} [{self.status}]"
