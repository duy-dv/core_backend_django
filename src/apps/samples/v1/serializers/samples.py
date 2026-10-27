"""Chuyển dữ liệu SampleItem sang JSON và kiểm tra dữ liệu gửi lên."""

from rest_framework import serializers

from apps.samples.models import SampleItem


class SampleItemMinimalSerializer(serializers.ModelSerializer):
    """Dữ liệu rút gọn; không trả mô tả dài và metadata."""

    class Meta:
        model = SampleItem
        fields = ("id", "title", "status")
        read_only_fields = fields


class SampleItemSerializer(serializers.ModelSerializer):
    # Dùng chung cho CRUD; các trường bên dưới chỉ do máy chủ gán.
    class Meta:
        model = SampleItem
        fields = (
            "id",
            "title",
            "description",
            "status",
            "priority",
            "metadata",
            "owner",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "owner",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        )
