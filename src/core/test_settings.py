"""Cấu hình riêng cho kiểm thử, không dùng khi chạy ứng dụng thật."""

from core.settings import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-only-secret-key-not-for-deployment-01234567890123456789"
ALLOWED_HOSTS = ["testserver", "localhost"]
if not env_bool("TEST_POSTGRES"):  # noqa: F405
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
# Chỉ dùng bộ băm nhanh này trong test để rút ngắn thời gian chạy.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
