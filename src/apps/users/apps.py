from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
    verbose_name = "Quản lý người dùng"

    def ready(self):
        from apps.users import schema  # noqa: F401
