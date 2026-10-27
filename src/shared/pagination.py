"""
Phân trang để API không trả toàn bộ dữ liệu trong một lần gọi.
"""

from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Mặc định 10 bản ghi/trang; client có thể tăng nhưng không quá 100."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
