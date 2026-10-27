"""Cấu hình khi triển khai thật; người mới có thể đọc file này sau."""

import os

from django.core.exceptions import ImproperlyConfigured

from core.settings import *  # noqa: F403

DEBUG = False

# Không cho chạy với khóa mặc định hoặc danh sách host mở cho tất cả.
if (
    not os.getenv("SECRET_KEY")
    or len(SECRET_KEY) < 50  # noqa: F405
    or SECRET_KEY.startswith("django-insecure-")  # noqa: F405
):
    raise ImproperlyConfigured("Cần SECRET_KEY ngẫu nhiên dài ít nhất 50 ký tự.")
if not os.getenv("ALLOWED_HOSTS") or "*" in ALLOWED_HOSTS:  # noqa: F405
    raise ImproperlyConfigured("Cần khai báo ALLOWED_HOSTS cụ thể.")
if not os.getenv("POSTGRES_DB") or not os.getenv("POSTGRES_PASSWORD"):
    raise ImproperlyConfigured("Cần cấu hình PostgreSQL khi triển khai thật.")

SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Chỉ tin header này khi reverse proxy xóa header của client và tự gán lại.
if env_bool("TRUST_PROXY_SSL_HEADER"):  # noqa: F405
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Schema JSON trên server chỉ cho quản trị viên gọi bằng Bearer JWT.
SPECTACULAR_SETTINGS = {
    **SPECTACULAR_SETTINGS,  # noqa: F405
    "SERVE_PERMISSIONS": ["shared.permissions.IsAdmin"],
    "SERVE_AUTHENTICATION": ["apps.users.authentication.ActiveJWTAuthentication"],
}
