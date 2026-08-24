from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient


class TokenObtainViewTests(TestCase):
    def setUp(self) -> None:
        self.api_client = APIClient()
        self.user_model = get_user_model()

    def test_returns_jwt_pair(self) -> None:
        self.user_model.objects.create_user("test@example.com", "StrongPass!2026")

        response = self.api_client.post(
            "/api/accounts/token/obtain",
            {
                "email": " TEST@Example.COM ",
                "password": "StrongPass!2026",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())
        self.assertNotIn("sessionid", self.api_client.cookies)

    def test_rejects_invalid_or_deleted_accounts(self) -> None:
        self.user_model.objects.create_user(
            "deleted@example.com",
            "StrongPass!2026",
            deleted_at=timezone.now(),
        )
        self.user_model.objects.create_user(
            "inactive@example.com",
            "StrongPass!2026",
            is_active=False,
        )

        failed_response = APIClient().post(
            "/api/accounts/token/obtain",
            {
                "email": "missing@example.com",
                "password": "StrongPass!2026",
            },
            format="json",
        )

        self.assertEqual(failed_response.status_code, 401)
        self.assertEqual(failed_response.json()["code"], "no_active_account")
        self.assertEqual(
            failed_response.json()["details"],
            {},
        )

        deleted_response = APIClient().post(
            "/api/accounts/token/obtain",
            {
                "email": "deleted@example.com",
                "password": "StrongPass!2026",
            },
            format="json",
        )

        self.assertEqual(deleted_response.status_code, 401)
        self.assertEqual(deleted_response.json()["code"], "no_active_account")
        self.assertEqual(deleted_response.json()["details"], {})

        inactive_response = APIClient().post(
            "/api/accounts/token/obtain",
            {
                "email": "inactive@example.com",
                "password": "StrongPass!2026",
            },
            format="json",
        )

        self.assertEqual(inactive_response.status_code, 401)
        self.assertEqual(inactive_response.json()["code"], "no_active_account")
        self.assertEqual(inactive_response.json()["details"], {})


class TokenRefreshViewTests(TestCase):
    def setUp(self) -> None:
        self.api_client = APIClient()
        self.user_model = get_user_model()

    def test_returns_new_access_token(self) -> None:
        self.user_model.objects.create_user("test@example.com", "StrongPass!2026")
        login_response = self.api_client.post(
            "/api/accounts/token/obtain",
            {
                "email": "test@example.com",
                "password": "StrongPass!2026",
            },
            format="json",
        )

        response = self.api_client.post(
            "/api/accounts/token/refresh",
            {"refresh": login_response.json()["refresh"]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
