"""Kiểm tra danh sách UUID cho các thao tác dùng chung."""

from rest_framework import serializers


class BulkDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=False, max_length=100)


class SelectedIdsSerializer(serializers.Serializer):
    selected_ids = serializers.ListField(
        child=serializers.UUIDField(), max_length=100, default=list
    )
