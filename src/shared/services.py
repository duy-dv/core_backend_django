"""Nghiệp vụ dùng chung cho nhiều module."""

from django.core.exceptions import ValidationError
from django.db import transaction


@transaction.atomic
def delete_many(queryset, ids, *, check_permission):
    """Chỉ xóa khi mọi ID đều tồn tại trong phạm vi quyền và được phép xóa."""
    ids = set(ids)
    if not ids or len(ids) > 100:
        raise ValidationError({"ids": "Cần từ 1 đến 100 ID."})

    # Giữ queryset của người gọi; không truy vấn lại qua model.objects toàn cục.
    objects = list(queryset.select_for_update().filter(pk__in=ids))
    if len(objects) != len(ids):
        raise ValidationError({"ids": "Có bản ghi không tồn tại hoặc không được phép truy cập."})
    for obj in objects:
        check_permission(obj)

    # Kiểm tra hết trước khi xóa. Nếu có lỗi, transaction hoàn tác cả thao tác.
    queryset.filter(pk__in=ids).delete()
