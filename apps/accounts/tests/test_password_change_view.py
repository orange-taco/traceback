import json
from typing import Any

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.test import Client, TestCase


class PasswordChangeViewTests(TestCase):
    path = "/_allauth/browser/v1/account/password/change"

    def setUp(self) -> None:
        self.client = Client(enforce_csrf_checks=True)
        self.user = get_user_model().objects.create_user(
            "change@example.com", "old-valid-pass-123"
        )
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, primary=True, verified=True
        )

    def post(self, path: str, payload: dict[str, str]) -> Any:
        self.client.get("/_allauth/browser/v1/config")
        return self.client.post(
            path,
            data=json.dumps(payload),
            content_type="application/json",
            headers={"X-CSRFToken": self.client.cookies["csrftoken"].value},
        )

    def login(self, password: str) -> Any:
        return self.post(
            "/_allauth/browser/v1/auth/login",
            {"email": self.user.email, "password": password},
        )

    def test_change_preserves_current_session_and_invalidates_other_session(
        self,
    ) -> None:
        other_client = Client()
        other_client.force_login(self.user)
        self.assertEqual(self.login("old-valid-pass-123").status_code, 200)
        old_key = self.client.session.session_key

        response = self.post(
            self.path,
            {
                "current_password": "old-valid-pass-123",
                "new_password": "new-valid-pass-456",
            },
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json()["meta"]["is_authenticated"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new-valid-pass-456"))
        self.assertFalse(Session.objects.filter(session_key=old_key).exists())
        self.assertTrue(response.cookies["sessionid"]["httponly"])
        self.assertEqual(
            other_client.get("/_allauth/browser/v1/auth/session").status_code, 401
        )
        self.client.delete(
            "/_allauth/browser/v1/auth/session",
            headers={"X-CSRFToken": self.client.cookies["csrftoken"].value},
        )
        self.assertEqual(self.login("old-valid-pass-123").status_code, 400)
        self.assertEqual(self.login("new-valid-pass-456").status_code, 200)

    def test_anonymous_change_is_rejected(self) -> None:
        response = self.post(self.path, {"new_password": "new-valid-pass-456"})
        self.assertEqual(response.status_code, 401)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("old-valid-pass-123"))

    def test_missing_wrong_current_or_weak_new_password_is_rejected(self) -> None:
        self.login("old-valid-pass-123")
        for current, new in [
            ("", "new-valid-pass-456"),
            ("wrong-password", "new-valid-pass-456"),
            ("old-valid-pass-123", "short"),
        ]:
            with self.subTest(current=current, new=new):
                response = self.post(
                    self.path, {"current_password": current, "new_password": new}
                )
                self.assertEqual(response.status_code, 400)
                self.user.refresh_from_db()
                self.assertTrue(self.user.check_password("old-valid-pass-123"))

    def test_change_requires_csrf(self) -> None:
        self.login("old-valid-pass-123")
        response = self.client.post(
            self.path,
            data=json.dumps(
                {
                    "current_password": "old-valid-pass-123",
                    "new_password": "new-valid-pass-456",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("old-valid-pass-123"))
