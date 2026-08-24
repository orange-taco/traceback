from unittest import mock

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient


class SignupViewTests(TestCase):
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
