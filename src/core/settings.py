"""Cấu hình phát triển: chạy ngay với SQLite, không cần dịch vụ bên ngoài."""

import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Thư mục src; file .env nằm ngoài src, tại thư mục gốc dự án.
BASE_DIR = Path(__file__).resolve().parent.parent
if os.getenv("DJANGO_SETTINGS_MODULE") != "core.test_settings":
    load_dotenv(BASE_DIR.parent / ".env")


def env_bool(name, default=False):
    value = os.getenv(name, str(default)).lower()
    if value not in {"true", "false", "1", "0", "yes", "no"}:
        raise ImproperlyConfigured(f"{name} phải là True hoặc False.")
    return value in {"true", "1", "yes"}


def env_list(name, default=""):
    return [value.strip() for value in os.getenv(name, default).split(",") if value.strip()]


# DEBUG chỉ bật khi phát triển trên máy cá nhân.
DEBUG = env_bool("DEBUG", True)
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-local-development-only-change-before-deploy")
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Đăng ký các ứng dụng của Django, thư viện bên ngoài và module của dự án.
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "apps.users.apps.UsersConfig",
    "apps.samples.apps.SamplesConfig",
]
# Backend xác thực bằng Bearer JWT, không dùng session đăng nhập trình duyệt.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "core.urls"
# Backend thuần API: không có template engine hoặc giao diện HTML.
TEMPLATES = []
WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

# Để trống POSTGRES_DB thì dùng SQLite. Chỉ cấu hình PostgreSQL khi cần.
if os.getenv("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["POSTGRES_DB"],
            "USER": os.getenv("POSTGRES_USER", "django"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
            # Không giữ kết nối lâu giữa các request khi chạy ASGI.
            "CONN_MAX_AGE": 0,
            "OPTIONS": {"connect_timeout": 5},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Dùng model User của dự án thay cho model mặc định của Django.
AUTH_USER_MODEL = "users.User"
AUTHENTICATION_BACKENDS = ["apps.users.authentication.ActiveUserBackend"]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True
APPEND_SLASH = True

# Mặc định API yêu cầu đăng nhập; endpoint công khai phải khai báo AllowAny.
REST_FRAMEWORK = {
    # Chỉ trả JSON, tắt giao diện Browsable API của DRF.
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.users.authentication.ActiveJWTAuthentication"],
    "EXCEPTION_HANDLER": "shared.exceptions.handle.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "shared.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "100/hour", "user": "1000/hour", "auth": "20/minute"},
}
# Access dùng gọi API; refresh dùng lấy cặp token mới khi access hết hạn.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "15"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "CHECK_REVOKE_TOKEN": True,
}
SPECTACULAR_SETTINGS = {
    "TITLE": "Django Base API",
    "VERSION": "1.0.0",
    "DESCRIPTION": "Bộ khung Django + DRF cơ bản, có xác thực JWT và một module CRUD mẫu.",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}
# Chỉ cho phép frontend từ các địa chỉ đã khai báo trong .env.
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
# Cache mặc định của Django nằm trong bộ nhớ, đủ để chạy thử trên một tiến trình.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"standard": {"format": "{asctime} {levelname} {name}: {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "standard"}},
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
}
