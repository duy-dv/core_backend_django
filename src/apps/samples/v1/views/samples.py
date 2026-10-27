"""API CRUD mẫu để sao chép khi tạo một module nghiệp vụ mới."""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from apps.samples.models import SampleItem
from apps.samples.services import SampleItemService
from apps.samples.v1.serializers.samples import SampleItemMinimalSerializer, SampleItemSerializer
from shared.mixins import BulkDeleteMixin, MinimalMixin
from shared.permissions import is_admin
from shared.serializers import BulkDeleteSerializer


@extend_schema_view(
    minimal=extend_schema(responses={200: SampleItemMinimalSerializer(many=True)}),
)
class SampleItemViewSetV1(MinimalMixin, BulkDeleteMixin, viewsets.ModelViewSet):
    # ModelViewSet đã có sẵn list, retrieve, create, update và destroy.
    queryset = SampleItem.objects.all()
    serializer_class = SampleItemSerializer
    filterset_fields = ["status", "priority"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "title"]

    def get_serializer_class(self):
        if self.action == "minimal":
            return SampleItemMinimalSerializer
        if self.action == "delete_many":
            return BulkDeleteSerializer
        return SampleItemSerializer

    def check_delete_permission(self, obj):
        super().check_delete_permission(obj)
        SampleItemService.check_owner(obj, self.request.user)

    def get_queryset(self):
        """Admin xem tất cả; người dùng khác chỉ xem bản ghi của mình."""
        queryset = self.queryset.order_by("-created_at", "id")
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if is_admin(user):
            return queryset
        return queryset.filter(owner=user)

    def perform_create(self, serializer):
        # DRF đã validate dữ liệu; service xử lý việc lưu và gán người tạo.
        # Gán instance để DRF trả bản ghi vừa tạo, bao gồm cả ID.
        serializer.instance = SampleItemService.create_item(
            owner=self.request.user, **serializer.validated_data
        )

    def perform_update(self, serializer):
        serializer.instance = SampleItemService.update_item(
            item=serializer.instance, actor=self.request.user, data=serializer.validated_data
        )

    def perform_destroy(self, instance):
        SampleItemService.delete_item(item=instance, actor=self.request.user)
