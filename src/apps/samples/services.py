"""Nghiệp vụ ghi dữ liệu mẫu, dùng lại được từ API hoặc lệnh quản trị."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.samples.models import SampleItem
from shared.permissions import is_admin


class SampleItemService:
    # Chỉ các trường này được thay đổi; owner và thông tin tạo/sửa do máy chủ gán.
    writable_fields = {"title", "description", "priority", "status", "metadata"}

    @staticmethod
    def check_owner(item, actor):
        if (
            not actor.is_active
            or actor.is_locked
            or (item.owner_id != actor.pk and not is_admin(actor))
        ):
            raise PermissionDenied("Bạn không có quyền sửa bản ghi này.")

    @staticmethod
    @transaction.atomic
    def create_item(*, owner, **data):
        """Tạo bản ghi; transaction tự hoàn tác nếu xảy ra lỗi khi lưu."""
        if not owner.is_active or owner.is_locked:
            raise PermissionDenied
        if set(data) - SampleItemService.writable_fields:
            raise ValidationError("Trường dữ liệu không được hỗ trợ.")
        item = SampleItem(owner=owner, created_by=owner, updated_by=owner, **data)
        # Kiểm tra cả quy tắc của model, kể cả khi gọi service ngoài API.
        item.full_clean()
        item.save()
        return item

    @staticmethod
    @transaction.atomic
    def update_item(*, item, actor, data):
        # Khóa hàng trong giao dịch để tránh hai thao tác sửa/xóa chồng lên nhau.
        item = SampleItem.objects.select_for_update().get(pk=item.pk)
        SampleItemService.check_owner(item, actor)
        if set(data) - SampleItemService.writable_fields:
            raise ValidationError("Trường dữ liệu không được hỗ trợ.")
        for field, value in data.items():
            setattr(item, field, value)
        item.updated_by = actor
        # Kiểm tra cả quy tắc của model, kể cả khi gọi service ngoài API.
        item.full_clean()
        item.save()
        return item

    @staticmethod
    @transaction.atomic
    def delete_item(*, item, actor):
        # Khóa hàng trong giao dịch để tránh hai thao tác sửa/xóa chồng lên nhau.
        item = SampleItem.objects.select_for_update().get(pk=item.pk)
        SampleItemService.check_owner(item, actor)
        item.delete()
