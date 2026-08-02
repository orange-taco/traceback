from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class CustomerAccountAuthAPITests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user_model = get_user_model()

    def test_signup_creates_user_and_starts_session(self) -> None:
        response = self.client.post(
            "/api/accounts/signup",
            {
                "email": " TEST@Example.COM ",
                "password": "StrongPass!2026",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["authenticated"], True)
        self.assertEqual(body["user"]["email"], "test@example.com")
        self.assertEqual(body["user"]["email_verified"], False)
        self.assertTrue(body["user"]["username"].startswith("user_"))
        self.assertIn("sessionid", self.client.cookies)

        session_response = self.client.get("/api/accounts/session")

        self.assertEqual(session_response.status_code, 200)
        self.assertEqual(session_response.json()["authenticated"], True)
        self.assertEqual(session_response.json()["user"]["email"], "test@example.com")

    def test_signup_rejects_existing_email(self) -> None:
        self.user_model.objects.create_user("test@example.com", "StrongPass!2026")

        response = self.client.post(
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

    def test_login_starts_session_without_revealing_account_existence(self) -> None:
        self.user_model.objects.create_user("test@example.com", "StrongPass!2026")

        response = self.client.post(
            "/api/accounts/login",
            {
                "email": " TEST@Example.COM ",
                "password": "StrongPass!2026",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["authenticated"], True)
        self.assertEqual(response.json()["user"]["email"], "test@example.com")
        self.assertIn("sessionid", self.client.cookies)

        failed_response = APIClient().post(
            "/api/accounts/login",
            {
                "email": "missing@example.com",
                "password": "StrongPass!2026",
            },
            format="json",
        )

        self.assertEqual(failed_response.status_code, 400)
        self.assertEqual(failed_response.json()["code"], "invalid")
        self.assertEqual(
            failed_response.json()["details"],
            {"non_field_errors": ["Unable to sign in with the provided credentials."]},
        )

    def test_session_and_logout_for_anonymous_and_authenticated_users(self) -> None:
        anonymous_response = self.client.get("/api/accounts/session")

        self.assertEqual(anonymous_response.status_code, 200)
        self.assertEqual(
            anonymous_response.json(),
            {"authenticated": False, "user": None},
        )
        self.assertIn("csrftoken", self.client.cookies)

        user = self.user_model.objects.create_user(
            "test@example.com",
            "StrongPass!2026",
        )
        self.client.force_login(user)

        authenticated_response = self.client.get("/api/accounts/session")

        self.assertEqual(authenticated_response.status_code, 200)
        self.assertEqual(authenticated_response.json()["authenticated"], True)

        logout_response = self.client.post("/api/accounts/logout")

        self.assertEqual(logout_response.status_code, 204)
        session_response = self.client.get("/api/accounts/session")

        self.assertEqual(session_response.json()["authenticated"], False)
