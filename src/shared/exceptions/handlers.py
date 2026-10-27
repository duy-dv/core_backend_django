"""Trả JSON cho lỗi Django nằm ngoài quá trình xử lý của DRF."""

from django.http import JsonResponse


def bad_request(request, exception):
    return JsonResponse({"detail": "Yêu cầu không hợp lệ."}, status=400)


def permission_denied(request, exception):
    return JsonResponse({"detail": "Bạn không có quyền truy cập."}, status=403)


def not_found(request, exception):
    return JsonResponse({"detail": "Đường dẫn không tồn tại."}, status=404)


def server_error(request):
    # Không đưa chi tiết exception hoặc thông tin nội bộ ra client.
    return JsonResponse({"detail": "Có lỗi hệ thống."}, status=500)
