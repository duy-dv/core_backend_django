"""
Các giá trị lựa chọn chung cho vai trò, trạng thái và mức ưu tiên.
"""

from django.db import models


class Role(models.TextChoices):
    ADMIN = "admin", "Quản trị viên"
    MANAGER = "manager", "Quản lý"
    STAFF = "staff", "Nhân viên"


class CommonStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Đang hoạt động"
    INACTIVE = "INACTIVE", "Ngừng hoạt động"
    ARCHIVED = "ARCHIVED", "Đã lưu trữ"


class Priority(models.TextChoices):
    LOW = "LOW", "Thấp"
    MEDIUM = "MEDIUM", "Trung bình"
    HIGH = "HIGH", "Cao"
    CRITICAL = "CRITICAL", "Khẩn cấp"
