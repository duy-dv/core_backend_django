"""Kiểm tra đăng ký, phân quyền quản trị và vòng đời token."""

from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APITestCase

from apps.users.models import User
from shared.constants import Role

AUTH = "/api/v1/users/auth/"
PASSWORD = "Strong-pass-123!"


class UserAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email="staff@example.com", password=PASSWORD, full_name="Staff"
        )
        self.admin = User.objects.create_user(
            email="admin@example.com", password=PASSWORD, full_name="Admin", role=Role.ADMIN
        )

    def login(self):
        result = self.client.post(
            AUTH + "login/",
            {
                "email": self.user.email,
                "password": PASSWORD,
            },
        )
        self.assertEqual(result.status_code, 200, result.data)
        return result.data

    def test_public_user_create_cannot_grant_admin(self):
        response = self.client.post(
            "/api/v1/users/",
            {
                "email": "evil@example.com",
                "full_name": "Evil",
                "password": PASSWORD,
                "role": "admin",
            },
        )
        self.assertEqual(response.status_code, 401)
        self.assertFalse(User.objects.filter(email="evil@example.com").exists())

    def test_registration_rejects_privilege_fields(self):
        for field, value in {"role": "admin", "is_staff": True, "is_superuser": True}.items():
            response = self.client.post(
                AUTH + "register/",
                {
                    "email": "new@example.com",
                    "full_name": "New",
                    "password": PASSWORD,
                    field: value,
                },
                format="json",
            )
            self.assertEqual(response.status_code, 400)

    def test_registration_hashes_password_and_normalizes_email(self):
        response = self.client.post(
            AUTH + "register/",
            {
                "email": "NEW@EXAMPLE.COM",
                "full_name": "New",
                "password": PASSWORD,
            },
        )
        self.assertEqual(response.status_code, 201, response.data)
        user = User.objects.get(pk=response.data["id"])
        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.role, Role.STAFF)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertNotIn("password", response.data)

    def test_registration_rejects_weak_password_and_case_duplicate(self):
        for email, password in [
            ("weak@example.com", "1234567890"),
            ("STAFF@example.com", PASSWORD),
        ]:
            response = self.client.post(
                AUTH + "register/",
                {
                    "email": email,
                    "full_name": "New",
                    "password": password,
                },
            )
            self.assertEqual(response.status_code, 400)

    def test_login_error_does_not_enumerate_accounts(self):
        first = self.client.post(AUTH + "login/", {"email": self.user.email, "password": "wrong"})
        second = self.client.post(
            AUTH + "login/", {"email": "missing@example.com", "password": "wrong"}
        )
        self.assertEqual(first.status_code, 400)
        self.assertEqual(first.data, second.data)

    def test_password_whitespace_is_preserved(self):
        self.user.set_password("  Significant spaces 123!  ")
        self.user.save()
        response = self.client.post(
            AUTH + "login/",
            {
                "email": self.user.email,
                "password": "  Significant spaces 123!  ",
            },
        )
        self.assertEqual(response.status_code, 200, response.data)

    def test_access_token_me_and_restricted_user_directory(self):
        tokens = self.login()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + tokens["access"])
        self.assertEqual(self.client.get("/api/v1/users/me/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/users/").status_code, 403)

    def test_refresh_rotates_and_rejects_replay(self):
        tokens = self.login()
        response = self.client.post(AUTH + "refresh/", {"refresh": tokens["refresh"]})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertNotEqual(tokens["refresh"], response.data["refresh"])
        self.assertIn("access", response.data)
        self.assertEqual(
            self.client.post(
                AUTH + "refresh/",
                {
                    "refresh": tokens["refresh"],
                },
            ).status_code,
            400,
        )

    def test_logout_blacklists_refresh(self):
        tokens = self.login()
        self.assertEqual(
            self.client.post(
                AUTH + "logout/",
                {
                    "refresh": tokens["refresh"],
                },
            ).status_code,
            204,
        )
        self.assertEqual(
            self.client.post(
                AUTH + "refresh/",
                {
                    "refresh": tokens["refresh"],
                },
            ).status_code,
            400,
        )

    def test_invalid_and_missing_refresh_tokens(self):
        for endpoint in ["refresh/", "logout/"]:
            for data in [{}, {"refresh": "bad-token"}]:
                response = self.client.post(AUTH + endpoint, data)
                self.assertEqual(response.status_code, 400)
                self.assertIn("errors", response.data)

    def test_lock_blocks_existing_access_refresh_and_login(self):
        tokens = self.login()
        self.user.is_locked = True
        self.user.save()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + tokens["access"])
        self.assertEqual(self.client.get("/api/v1/users/me/").status_code, 401)
        self.assertEqual(
            self.client.post(
                AUTH + "refresh/",
                {
                    "refresh": tokens["refresh"],
                },
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                AUTH + "login/",
                {
                    "email": self.user.email,
                    "password": PASSWORD,
                },
            ).status_code,
            400,
        )

    def test_deactivation_blocks_refresh(self):
        tokens = self.login()
        self.user.is_active = False
        self.user.save()
        self.assertEqual(
            self.client.post(
                AUTH + "refresh/",
                {
                    "refresh": tokens["refresh"],
                },
            ).status_code,
            400,
        )

    def test_password_change_revokes_access_and_refresh(self):
        tokens = self.login()
        self.user.set_password("Different-secure-password123!")
        self.user.save()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + tokens["access"])
        self.assertEqual(self.client.get("/api/v1/users/me/").status_code, 401)
        self.assertEqual(
            self.client.post(
                AUTH + "refresh/",
                {
                    "refresh": tokens["refresh"],
                },
            ).status_code,
            400,
        )

    def test_deleted_user_refresh_is_client_error(self):
        tokens = self.login()
        self.user.delete()
        self.assertEqual(
            self.client.post(
                AUTH + "refresh/",
                {
                    "refresh": tokens["refresh"],
                },
            ).status_code,
            400,
        )

    def test_admin_create_update_and_audit(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/users/",
            {
                "email": "manager@example.com",
                "password": PASSWORD,
                "full_name": "Manager",
                "role": "manager",
            },
        )
        self.assertEqual(response.status_code, 201, response.data)
        user = User.objects.get(pk=response.data["id"])
        self.assertEqual(user.created_by, self.admin)
        response = self.client.patch(f"/api/v1/users/{user.pk}/", {"is_locked": True})
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.updated_by, self.admin)
        self.assertTrue(user.is_locked)

    def test_admin_cannot_delete_self_or_modify_superuser(self):
        root = User.objects.create_superuser("root@example.com", PASSWORD, full_name="Root")
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.delete(f"/api/v1/users/{self.admin.pk}/").status_code, 403)
        self.assertEqual(
            self.client.patch(
                f"/api/v1/users/{root.pk}/",
                {
                    "is_active": False,
                },
            ).status_code,
            403,
        )

    def test_auth_throttle(self):
        for _ in range(20):
            self.client.post(AUTH + "login/", {})
        self.assertEqual(self.client.post(AUTH + "login/", {}).status_code, 429)


class UserModelTests(TestCase):
    def test_superuser_flags_are_required(self):
        for values in [{"is_staff": False}, {"is_superuser": False}, {"role": Role.STAFF}]:
            with self.assertRaises(ValueError):
                User.objects.create_superuser("root@example.com", PASSWORD, **values)

    def test_database_case_insensitive_email_constraint(self):
        User.objects.create_user("same@example.com", PASSWORD)
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.bulk_create([User(email="SAME@example.com", full_name="Same")])
