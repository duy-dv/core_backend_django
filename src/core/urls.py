"""Đường dẫn backend: API nghiệp vụ, kiểm tra hoạt động và schema JSON."""

from django.urls import include, path
from drf_spectacular.views import SpectacularJSONAPIView

from core.health import live, ready

urlpatterns = [
    path("health/live/", live, name="health-live"),
    path("health/ready/", ready, name="health-ready"),
    path("api/v1/users/", include("apps.users.v1.urls")),
    path("api/v1/samples/", include("apps.samples.v1.urls")),
    # Xuất OpenAPI để nhập vào Swagger/Postman chạy bên ngoài backend.
    path("schema/", SpectacularJSONAPIView.as_view(), name="openapi-schema"),
]

# Lỗi nằm ngoài DRF cũng trả JSON khi DEBUG=False.
handler400 = "shared.exceptions.handlers.bad_request"
handler403 = "shared.exceptions.handlers.permission_denied"
handler404 = "shared.exceptions.handlers.not_found"
handler500 = "shared.exceptions.handlers.server_error"
