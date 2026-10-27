"""Kiểm tra minimal và xóa nhiều bản ghi không làm vượt phạm vi quyền."""

import uuid

from django.core.cache import cache
from rest_framework.test import APITestCase

from apps.samples.models import SampleItem
from apps.users.models import User


class BulkMinimalTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user("owner@example.com", "Strong-pass-123!")
        self.other = User.objects.create_user("other@example.com", "Strong-pass-123!")
        self.admin = User.objects.create_user("admin@example.com", "Strong-pass-123!", role="admin")
        self.item = SampleItem.objects.create(title="Của tôi", owner=self.owner)
        self.foreign = SampleItem.objects.create(title="Của người khác", owner=self.other)

    def test_anonymous_cannot_use_actions(self):
        for resource in ["users", "samples"]:
            self.assertEqual(self.client.get(f"/api/v1/{resource}/minimal/").status_code, 401)
            response = self.client.post(
                f"/api/v1/{resource}/delete-many/", {"ids": []}, format="json"
            )
            self.assertEqual(response.status_code, 401)

    def test_sample_minimal_is_compact_and_scoped(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get("/api/v1/samples/minimal/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(set(response.data["results"][0]), {"id", "title", "status"})
        self.assertEqual(response.data["results"][0]["id"], str(self.item.pk))

    def test_selected_ids_do_not_leak_other_users_items(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(
            "/api/v1/samples/minimal/",
            {
                "search": "không tìm thấy",
                "selected_ids": f"{self.item.pk},{self.item.pk},{self.foreign.pk}",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual([row["id"] for row in response.data["results"]], [str(self.item.pk)])

    def test_minimal_pagination_and_selected_item(self):
        self.client.force_authenticate(self.owner)
        newer = SampleItem.objects.create(title="Mới", owner=self.owner)
        response = self.client.get(
            "/api/v1/samples/minimal/",
            {
                "page_size": 1,
                "selected_ids": str(self.item.pk),
                "ordering": "-title",
            },
        )
        self.assertEqual(response.data["count"], 2)
        self.assertIsNotNone(response.data["next"])
        self.assertCountEqual(
            [row["id"] for row in response.data["results"]],
            [str(self.item.pk), str(newer.pk)],
        )

    def test_minimal_validates_uuid_and_limit(self):
        self.client.force_authenticate(self.owner)
        for value in ["không-phải-uuid", ",".join([str(self.item.pk)] * 101)]:
            response = self.client.get("/api/v1/samples/minimal/", {"selected_ids": value})
            self.assertEqual(response.status_code, 400)

    def test_mixed_owner_bulk_request_deletes_nothing(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            "/api/v1/samples/delete-many/",
            {
                "ids": [str(self.item.pk), str(self.foreign.pk)],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(SampleItem.objects.count(), 2)

    def test_valid_bulk_delete_and_duplicate_ids(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            "/api/v1/samples/delete-many/",
            {
                "ids": [str(self.item.pk), str(self.item.pk)],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertFalse(SampleItem.objects.filter(pk=self.item.pk).exists())
        self.assertTrue(SampleItem.objects.filter(pk=self.foreign.pk).exists())

    def test_invalid_bulk_request_deletes_nothing(self):
        self.client.force_authenticate(self.owner)
        for ids in [
            [],
            ["invalid"],
            [str(self.item.pk), str(uuid.uuid4())],
            [str(self.item.pk)] * 101,
        ]:
            response = self.client.post("/api/v1/samples/delete-many/", {"ids": ids}, format="json")
            self.assertEqual(response.status_code, 400)
        self.assertEqual(SampleItem.objects.count(), 2)

    def test_admin_can_bulk_delete_samples_from_multiple_owners(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/samples/delete-many/",
            {
                "ids": [str(self.item.pk), str(self.foreign.pk)],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(SampleItem.objects.exists())

    def test_user_actions_require_admin(self):
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get("/api/v1/users/minimal/").status_code, 403)
        response = self.client.post(
            "/api/v1/users/delete-many/",
            {
                "ids": [str(self.other.pk)],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_user_minimal_and_valid_bulk_delete(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/v1/users/minimal/", {"search": self.other.email})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data["results"][0]), {"id", "email", "full_name", "role"})
        response = self.client.post(
            "/api/v1/users/delete-many/",
            {
                "ids": [str(self.other.pk)],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(pk=self.other.pk).exists())

    def test_user_bulk_cannot_delete_self_or_superuser(self):
        root = User.objects.create_superuser("root@example.com", "Strong-pass-123!")
        self.client.force_authenticate(self.admin)
        for protected in [self.admin, root]:
            response = self.client.post(
                "/api/v1/users/delete-many/",
                {
                    "ids": [str(self.other.pk), str(protected.pk)],
                },
                format="json",
            )
            self.assertEqual(response.status_code, 403)
            self.assertTrue(User.objects.filter(pk=self.other.pk).exists())
