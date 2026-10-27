from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """Giữ đầy đủ lỗi theo trường; không trả nội dung lỗi hệ thống ngoài dự kiến."""
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)
    response = exception_handler(exc, context)
    if response is not None:
        details = response.data
        response.data = {
            "detail": details.get("detail", "Yêu cầu không hợp lệ.")
            if isinstance(details, dict)
            else "Yêu cầu không hợp lệ.",
            "errors": details,
        }
    return response
