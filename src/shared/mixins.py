"""Hai chức năng API dùng lại được: dữ liệu rút gọn và xóa nhiều bản ghi."""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from shared.serializers import BulkDeleteSerializer, SelectedIdsSerializer
from shared.services import delete_many


class MinimalMixin:
    @extend_schema(
        parameters=[
            OpenApiParameter(
                "selected_ids", str, description="Tối đa 100 UUID, phân cách bằng dấu phẩy"
            ),
        ]
    )
    @action(detail=False, methods=["GET"], url_path="minimal")
    def minimal(self, request):
        """Trả dữ liệu rút gọn, có phân trang, để frontend dùng cho ô lựa chọn."""
        raw_ids = request.query_params.get("selected_ids", "")
        params = SelectedIdsSerializer(
            data={"selected_ids": [value.strip() for value in raw_ids.split(",") if value.strip()]}
        )
        params.is_valid(raise_exception=True)

        # get_queryset giới hạn quyền; filter_queryset áp dụng bộ lọc/tìm kiếm.
        allowed_queryset = self.get_queryset()
        queryset = self.filter_queryset(allowed_queryset)
        page = self.paginate_queryset(queryset)
        objects = list(page if page is not None else queryset)
        missing_ids = set(params.validated_data["selected_ids"]) - {obj.pk for obj in objects}
        # Bổ sung mục đã chọn ngoài kết quả tìm kiếm, nhưng không vượt quyền đọc.
        selected = list(allowed_queryset.filter(pk__in=missing_ids))
        data = self.get_serializer(selected + objects, many=True).data
        if page is not None:
            return self.get_paginated_response(data)
        return Response(data)


class BulkDeleteMixin:
    def check_delete_permission(self, obj):
        """Module có quy tắc xóa riêng cần ghi đè hàm này."""
        self.check_object_permissions(self.request, obj)

    @extend_schema(request=BulkDeleteSerializer, responses={204: None})
    @action(detail=False, methods=["POST"], url_path="delete-many")
    def delete_many(self, request):
        """Xóa tối đa 100 bản ghi; một ID sai thì không xóa bản ghi nào."""
        serializer = BulkDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        delete_many(
            self.get_queryset(),
            serializer.validated_data["ids"],
            check_permission=self.check_delete_permission,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
