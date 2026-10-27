"""Chỉ kiểm tra tình huống refresh đồng thời khi chạy trên PostgreSQL."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection
from django.test import TransactionTestCase

from apps.users.models import User
from apps.users.services import UserService


@skipUnless(connection.vendor == "postgresql", "Cần PostgreSQL để kiểm tra khóa hàng")
class RefreshConcurrencyTests(TransactionTestCase):
    def test_only_one_concurrent_refresh_succeeds(self):
        user = User.objects.create_user("race@example.com", "Strong-pass-123!", full_name="Race")
        token = UserService.issue_tokens(user)["refresh"]
        barrier = Barrier(2)

        def refresh():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    UserService.refresh_access_token(token)
                    return "accepted"
                except ValidationError:
                    return "rejected"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(refresh) for _ in range(2)]
            results = [future.result(timeout=20) for future in futures]
        self.assertCountEqual(results, ["accepted", "rejected"])
