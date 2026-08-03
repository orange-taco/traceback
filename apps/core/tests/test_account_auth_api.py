from unittest import mock

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient


class CustomerAccountAuthAPITests(TestCase):
    def setUp(self) -> None:
        self.api_client = APIClient()
        self.user_model = get_user_model()

    def test_signup_creates_user(self) -> None:
        response = self.api_client.post(
            "/api/accounts/signup",
            {
                "email": " TEST@Example.COM ",
                "password": "StrongPass!2026",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content, b"")
        user = self.user_model.objects.get(email="test@example.com")
        self.assertTrue(user.username.startswith("user_"))
        self.assertNotIn("sessionid", self.api_client.cookies)

    def test_signup_rejects_existing_email(self) -> None:
        self.user_model.objects.create_user("test@example.com", "StrongPass!2026")

        response = self.api_client.post(
            "/api/accounts/signup",
            {
                "email": "test@example.com",
                "password": "StrongPass!2026",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid")
        self.assertIn("email", response.json()["details"])

    def test_signup_rejects_email_unique_race_as_field_error(self) -> None:
        with mock.patch.object(
            self.user_model.objects,
            "create_user",
            side_effect=IntegrityError,
        ):
            response = self.api_client.post(
                "/api/accounts/signup",
                {
                    "email": "test@example.com",
                    "password": "StrongPass!2026",
                },
                format="json",
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid")
        self.assertEqual(
            response.json()["details"],
            {"email": ["This email is already registered."]},
        )

    def test_signup_rejects_weak_password_as_field_error(self) -> None:
        response = self.api_client.post(
            "/api/accounts/signup",
            {
                "email": "test@example.com",
                "password": "12345678",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid")
        self.assertIn("password", response.json()["details"])
        self.assertIsInstance(response.json()["details"]["password"], list)

    def test_token_obtain_returns_jwt_pair(self) -> None:
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

    def test_token_obtain_rejects_invalid_or_deleted_accounts(self) -> None:
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

    def test_refresh_token_returns_new_access_token(self) -> None:
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
