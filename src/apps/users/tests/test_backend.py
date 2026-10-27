"""Kiểm tra backend không phụ thuộc template, session hay giao diện Django."""

from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.users.models import User


class BackendOnlyTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_no_template_or_browser_apps(self):
        self.assertEqual(settings.TEMPLATES, [])
        for app in ["admin", "sessions", "messages", "staticfiles"]:
            self.assertNotIn(f"django.contrib.{app}", settings.INSTALLED_APPS)
        self.assertNotIn(
            "django.contrib.sessions.middleware.SessionMiddleware", settings.MIDDLEWARE
        )

    def test_removed_ui_routes_return_json_404(self):
        for path in ["/admin/", "/docs/", "/redoc/"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response["Content-Type"], "application/json")

    def test_api_returns_json_without_session_cookie(self):
        user = User.objects.create_user("api@example.com", "Strong-pass-123!", full_name="API")
        response = self.client.post(
            "/api/v1/users/auth/login/",
            {
                "email": user.email,
                "password": "Strong-pass-123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertNotIn("sessionid", response.cookies)

    def test_api_does_not_render_html(self):
        response = self.client.get("/api/v1/samples/", HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 406)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_openapi_schema_is_json(self):
        response = self.client.get("/schema/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.oai.openapi+json")
        self.assertIn("openapi", response.json())
        self.assertNotIn("/admin/", response.json()["paths"])

    @override_settings(DEBUG=False)
    def test_generic_errors_do_not_expose_exception_details(self):
        from django.test import RequestFactory

        from shared.exceptions.handlers import bad_request, permission_denied, server_error

        request = RequestFactory().get("/")
        for handler, status in [(bad_request, 400), (permission_denied, 403)]:
            response = handler(request, ValueError("internal-secret"))
            self.assertEqual(response.status_code, status)
            self.assertNotIn(b"internal-secret", response.content)
        self.assertEqual(server_error(request).status_code, 500)
