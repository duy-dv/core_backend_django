"""Đảm bảo Swagger mô tả đúng xác thực JWT và phản hồi phân trang."""

from django.test import SimpleTestCase
from drf_spectacular.generators import SchemaGenerator


class SchemaContractTests(SimpleTestCase):
    def test_crud_list_is_paginated_and_jwt_is_documented(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        for path in [
            "/api/v1/users/",
            "/api/v1/samples/",
            "/api/v1/users/minimal/",
            "/api/v1/samples/minimal/",
        ]:
            operation = schema["paths"][path]["get"]
            self.assertIn({"jwtAuth": []}, operation["security"])
            response = operation["responses"]["200"]["content"]["application/json"]["schema"]
            component = schema["components"]["schemas"][response["$ref"].split("/")[-1]]
            self.assertIn("results", component["properties"])
            self.assertIn("count", component["properties"])

    def test_optional_features_are_not_part_of_the_base(self):
        paths = SchemaGenerator().get_schema(request=None, public=True)["paths"]
        self.assertNotIn("/api/v1/users/auth/login-google/", paths)
        for resource in ["users", "samples"]:
            self.assertIn("post", paths[f"/api/v1/{resource}/delete-many/"])
            self.assertIn("get", paths[f"/api/v1/{resource}/minimal/"])
