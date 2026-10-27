"""Kiểm tra module CRUD mẫu: dữ liệu hợp lệ, chủ sở hữu và quyền admin."""

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from rest_framework.test import APIClient, APITestCase

from apps.samples.models import SampleItem
from apps.samples.services import SampleItemService
from apps.users.models import User
from shared.constants import Role


class SampleAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(
            "owner@example.com", "Strong-pass-123!", full_name="Owner"
        )
        self.other = User.objects.create_user(
            "other@example.com", "Strong-pass-123!", full_name="Other"
        )
        self.admin = User.objects.create_user(
            "admin@example.com", "Strong-pass-123!", full_name="Admin", role=Role.ADMIN
        )
        self.item = SampleItemService.create_item(owner=self.owner, title="Owned")
        self.foreign = SampleItemService.create_item(owner=self.other, title="Private")
        self.client.force_authenticate(self.owner)

    def test_anonymous_denied(self):
        # Client mới không có JWT; không gọi logout vì backend không dùng session.
        self.client = APIClient()
        self.assertEqual(self.client.get("/api/v1/samples/").status_code, 401)

    def test_list_and_detail_only_show_owned_items(self):
        listing = self.client.get("/api/v1/samples/")
        self.assertEqual(listing.data["count"], 1)
        self.assertEqual(listing.data["results"][0]["id"], str(self.item.pk))
        self.assertEqual(self.client.get(f"/api/v1/samples/{self.foreign.pk}/").status_code, 404)

    def test_admin_can_read_all_items(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get("/api/v1/samples/").data["count"], 2)
        self.assertEqual(self.client.get(f"/api/v1/samples/{self.foreign.pk}/").status_code, 200)

    def test_create_uses_current_user_for_owner_and_audit(self):
        response = self.client.post(
            "/api/v1/samples/",
            {
                "title": "New",
                "owner": str(self.other.pk),
                "created_by": str(self.other.pk),
                "metadata": {"key": 1},
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        item = SampleItem.objects.get(pk=response.data["id"])
        self.assertEqual(item.owner, self.owner)
        self.assertEqual(item.created_by, self.owner)
        self.assertEqual(item.updated_by, self.owner)

    def test_update_title_and_status(self):
        response = self.client.patch(
            f"/api/v1/samples/{self.item.pk}/",
            {
                "title": "Changed",
                "status": "ARCHIVED",
            },
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, "Changed")
        self.assertEqual(self.item.status, "ARCHIVED")
        self.assertEqual(self.item.updated_by, self.owner)

    def test_cross_owner_writes_denied(self):
        url = f"/api/v1/samples/{self.foreign.pk}/"
        self.assertEqual(self.client.patch(url, {"title": "Stolen"}).status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.foreign.refresh_from_db()
        self.assertEqual(self.foreign.title, "Private")

    def test_owner_can_delete(self):
        response = self.client.delete(f"/api/v1/samples/{self.item.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(SampleItem.objects.filter(pk=self.item.pk).exists())

    def test_admin_can_update_and_delete(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(f"/api/v1/samples/{self.item.pk}/", {"title": "Admin edit"})
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.updated_by, self.admin)
        self.assertEqual(self.client.delete(f"/api/v1/samples/{self.item.pk}/").status_code, 204)

    def test_validation_preserves_all_field_errors(self):
        response = self.client.post("/api/v1/samples/", {"title": "", "priority": "UNKNOWN"})
        self.assertEqual(response.status_code, 400)
        self.assertIsInstance(response.data["errors"]["title"], list)
        self.assertIn("priority", response.data["errors"])

    def test_filter_search_and_pagination(self):
        response = self.client.get(
            "/api/v1/samples/",
            {
                "status": "ACTIVE",
                "search": "Owned",
                "page_size": 1,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        response = self.client.get("/api/v1/samples/", {"search": "Private"})
        self.assertEqual(response.data["count"], 0)

    def test_service_checks_ownership_without_http(self):
        with self.assertRaises(PermissionDenied):
            SampleItemService.update_item(
                item=self.foreign, actor=self.owner, data={"title": "Stolen"}
            )

    def test_list_does_not_query_each_owner(self):
        for index in range(5):
            SampleItemService.create_item(owner=self.owner, title=f"Item {index}")
        # Một truy vấn đếm và một truy vấn lấy dữ liệu; không phát sinh theo số bản ghi.
        with self.assertNumQueries(2):
            response = self.client.get("/api/v1/samples/")
            self.assertEqual(response.status_code, 200)

    def test_health_endpoints(self):
        self.assertEqual(self.client.get("/health/live/").status_code, 200)
        self.assertEqual(self.client.get("/health/ready/").status_code, 200)
