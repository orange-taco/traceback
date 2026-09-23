import json
import re
from functools import partial
from typing import Any
from unittest.mock import patch
from urllib.parse import parse_qs, unquote, urlparse

from allauth.account.models import EmailAddress, get_emailconfirmation_model
from allauth.socialaccount.models import SocialAccount, SocialLogin
from allauth.socialaccount.providers.kakao.views import KakaoOAuth2Adapter
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core import mail
from django.http import HttpRequest
from django.test import Client, TestCase, override_settings
from django.utils.encoding import force_str


class HeadlessAccountAuthTests(TestCase):
    def setUp(self) -> None:
        self.client = Client(enforce_csrf_checks=True)
        self.user_model = get_user_model()

    def test_signup_requires_email_verification_before_password_login(self) -> None:
        response = self.post_json(
            "/_allauth/browser/v1/auth/signup",
            {"email": "NEW@Example.COM", "password": "valid-pass-123"},
        )

        self.assertEqual(response.status_code, 401)
        user = self.user_model.objects.get(email="new@example.com")
        address = EmailAddress.objects.get(user=user)
        self.assertFalse(address.verified)
        self.assertEqual(len(mail.outbox), 1)

        self.assertIn("http://localhost:5173/auth/verify-email/", mail.outbox[0].body)
        key = get_emailconfirmation_model().create(address).key
        response = self.post_json(
            "/_allauth/browser/v1/auth/email/verify",
            {"key": key},
        )

        self.assertEqual(response.status_code, 401, response.content)
        address.refresh_from_db()
        self.assertTrue(address.verified)
        self.assertFalse(response.json()["meta"]["is_authenticated"])

        response = self.post_json(
            "/_allauth/browser/v1/auth/login",
            {"email": user.email, "password": "valid-pass-123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["meta"]["is_authenticated"])

    @override_settings(ACCOUNT_RATE_LIMITS={"confirm_email": "10/180s/key"})
    def test_unverified_email_can_request_another_confirmation_link(self) -> None:
        response = self.post_json(
            "/_allauth/browser/v1/auth/signup",
            {"email": "resend@example.com", "password": "valid-pass-123"},
        )
        self.assertEqual(response.status_code, 401)
        mail.outbox.clear()

        response = self.post_json(
            "/accounts/email/verify/resend",
            {"email": "RESEND@EXAMPLE.COM"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/auth/verify-email/", mail.outbox[0].body)

    def test_confirmation_resend_does_not_reveal_unknown_email(self) -> None:
        response = self.post_json(
            "/accounts/email/verify/resend",
            {"email": "unknown@example.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_confirmation_resend_obeys_email_rate_limit(self) -> None:
        response = self.post_json(
            "/_allauth/browser/v1/auth/signup",
            {"email": "limited@example.com", "password": "valid-pass-123"},
        )
        self.assertEqual(response.status_code, 401)
        mail.outbox.clear()

        for _ in range(2):
            response = self.post_json(
                "/accounts/email/verify/resend",
                {"email": "limited@example.com"},
            )
            self.assertEqual(response.status_code, 200)

        self.assertEqual(len(mail.outbox), 1)

    def test_verified_user_can_login_read_session_and_logout(self) -> None:
        user = self.user_model.objects.create_user(
            "user@example.com",
            "valid-pass-123",
        )
        EmailAddress.objects.create(
            user=user,
            email=user.email,
            primary=True,
            verified=True,
        )

        response = self.post_json(
            "/_allauth/browser/v1/auth/login",
            {"email": user.email, "password": "valid-pass-123"},
        )

        self.assertEqual(response.status_code, 200)
        session = self.client.get("/_allauth/browser/v1/auth/session")
        self.assertEqual(session.status_code, 200)
        self.assertEqual(session.json()["data"]["user"]["email"], user.email)
        session_key = self.client.session.session_key
        self.assertTrue(Session.objects.filter(session_key=session_key).exists())

        response = self.delete("/_allauth/browser/v1/auth/session")

        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()["meta"]["is_authenticated"])

        self.assertFalse(Session.objects.filter(session_key=session_key).exists())
        self.assertEqual(
            self.client.get("/_allauth/browser/v1/auth/session").status_code, 401
        )

    def test_authenticated_user_can_disconnect_local_social_account(self) -> None:
        user = self.user_model.objects.create_user(
            "disconnect@example.com", "valid-pass-123"
        )
        EmailAddress.objects.create(
            user=user, email=user.email, primary=True, verified=True
        )
        account = SocialAccount.objects.create(user=user, provider="kakao", uid="uid-1")
        self.client.force_login(user)

        response = self.client.get("/_allauth/browser/v1/account/providers")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"][0]["uid"], account.uid)

        with patch("apps.accounts.adapters.unlink_kakao_user") as unlink:
            response = self.delete(
                "/_allauth/browser/v1/account/providers",
                {"provider": "kakao", "account": account.uid},
            )
        self.assertEqual(response.status_code, 200)
        unlink.assert_called_once_with(account.uid)
        self.assertFalse(SocialAccount.objects.filter(pk=account.pk).exists())

    def test_social_only_user_cannot_disconnect_without_password(self) -> None:
        user = self.user_model.objects.create_user(
            "social-only@example.com", password=None
        )
        EmailAddress.objects.create(
            user=user, email=user.email, primary=True, verified=True
        )
        account = SocialAccount.objects.create(
            user=user, provider="kakao", uid="uid-only"
        )
        self.client.force_login(user)

        response = self.delete(
            "/_allauth/browser/v1/account/providers",
            {"provider": "kakao", "account": account.uid},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["errors"][0]["code"], "no_password")
        self.assertTrue(SocialAccount.objects.filter(pk=account.pk).exists())

    def test_account_delete_anonymizes_user_and_clears_local_auth_state(self) -> None:
        user = self.user_model.objects.create_user(
            "delete@example.com", "valid-pass-123"
        )
        EmailAddress.objects.create(
            user=user, email=user.email, primary=True, verified=True
        )
        SocialAccount.objects.create(user=user, provider="kakao", uid="uid-delete")
        self.client.force_login(user)
        self.get_csrf_token()

        with patch("apps.accounts.services.unlink_kakao_user") as unlink:
            response = self.client.delete(
                "/accounts/delete",
                headers={"X-CSRFToken": self.client.cookies["csrftoken"].value},
            )

        self.assertEqual(response.status_code, 204)
        unlink.assert_called_once_with("uid-delete")
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertIsNotNone(user.deleted_at)
        self.assertTrue(user.email.startswith("deleted-"))
        self.assertLessEqual(len(user.username), 32)
        self.assertFalse(user.has_usable_password())
        self.assertFalse(EmailAddress.objects.filter(user=user).exists())
        self.assertFalse(SocialAccount.objects.filter(user=user).exists())
        self.assertEqual(
            self.client.get("/_allauth/browser/v1/auth/session").status_code, 401
        )

    def test_account_delete_requires_authentication_and_csrf(self) -> None:
        response = self.client.delete("/accounts/delete")
        self.assertEqual(response.status_code, 403)

        user = self.user_model.objects.create_user(
            "csrf-delete@example.com", "valid-pass-123"
        )
        self.client.force_login(user)
        response = self.client.delete("/accounts/delete")
        self.assertEqual(response.status_code, 403)

    def test_unverified_user_cannot_complete_password_login(self) -> None:
        user = self.user_model.objects.create_user(
            "pending@example.com",
            "valid-pass-123",
        )
        EmailAddress.objects.create(
            user=user,
            email=user.email,
            primary=True,
            verified=False,
        )

        response = self.post_json(
            "/_allauth/browser/v1/auth/login",
            {"email": user.email, "password": "valid-pass-123"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()["meta"]["is_authenticated"])

    def test_password_reset_link_changes_password(self) -> None:
        user = self.user_model.objects.create_user(
            "reset@example.com",
            "old-valid-pass-123",
        )
        EmailAddress.objects.create(
            user=user,
            email=user.email,
            primary=True,
            verified=True,
        )

        response = self.post_json(
            "/_allauth/browser/v1/auth/password/request",
            {"email": user.email},
        )

        self.assertEqual(response.status_code, 200)
        key = self.extract_mail_key(r"/auth/password/reset/([^\s/]+)")
        response = self.post_json(
            "/_allauth/browser/v1/auth/password/reset",
            {"key": key, "password": "new-valid-pass-123"},
        )

        self.assertEqual(response.status_code, 401, response.content)
        self.assertFalse(response.json()["meta"]["is_authenticated"])
        self.assertNotIn("_auth_user_id", self.client.session)
        user.refresh_from_db()
        self.assertTrue(user.check_password("new-valid-pass-123"))

    def post_json(self, path: str, payload: dict[str, str]) -> Any:
        csrf_token = self.get_csrf_token()
        return self.client.post(
            path,
            data=json.dumps(payload),
            content_type="application/json",
            headers={"X-CSRFToken": csrf_token},
        )

    def delete(self, path: str, payload: dict[str, str] | None = None) -> Any:
        csrf_token = self.get_csrf_token()
        return self.client.delete(
            path,
            data=json.dumps(payload or {}),
            content_type="application/json",
            headers={"X-CSRFToken": csrf_token},
        )

    def get_csrf_token(self) -> str:
        response = self.client.get("/_allauth/browser/v1/config")
        self.assertEqual(response.status_code, 200)
        return self.client.cookies["csrftoken"].value

    def extract_mail_key(self, pattern: str) -> str:
        match = re.search(pattern, force_str(mail.outbox[-1].body))
        assert match is not None
        return unquote(match.group(1))


class KakaoProviderRedirectTests(TestCase):
    @override_settings(
        CSRF_TRUSTED_ORIGINS=["http://localhost:5173"],
        SOCIALACCOUNT_PROVIDERS={
            "kakao": {
                "APPS": [
                    {
                        "client_id": "test-rest-api-key",
                        "secret": "test-client-secret",
                        "key": "",
                    }
                ],
                "SCOPE": ["account_email"],
                "EMAIL_AUTHENTICATION": True,
            }
        },
        SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT=True,
    )
    def test_redirect_uses_allauth_state_backend_callback_and_required_scopes(
        self,
    ) -> None:
        client = Client(enforce_csrf_checks=True)
        client.get("/_allauth/browser/v1/config")

        response = client.post(
            "/_allauth/browser/v1/auth/provider/redirect",
            {
                "provider": "kakao",
                "callback_url": "http://localhost:5173/auth/kakao/callback",
                "process": "login",
                "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
            },
        )

        self.assertEqual(response.status_code, 302)
        redirect = urlparse(response["Location"])
        query = parse_qs(redirect.query)
        self.assertEqual(redirect.netloc, "kauth.kakao.com")
        self.assertTrue(query["state"][0])
        self.assertIn("/accounts/kakao/login/callback/", query["redirect_uri"][0])
        self.assertEqual(
            set(query["scope"][0].split()),
            {"account_email"},
        )


@override_settings(
    CSRF_TRUSTED_ORIGINS=["http://localhost:5173"],
    SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT=True,
    SOCIALACCOUNT_PROVIDERS={
        "kakao": {
            "APPS": [
                {
                    "client_id": "test-rest-api-key",
                    "secret": "test-client-secret",
                    "key": "",
                }
            ],
            "EMAIL_AUTHENTICATION": True,
        }
    },
)
class KakaoAccountLinkingTests(TestCase):
    def test_verified_email_connects_to_existing_password_account(self) -> None:
        user = get_user_model().objects.create_user(
            "owner@example.com",
            "valid-pass-123",
        )
        EmailAddress.objects.create(
            user=user,
            email=user.email,
            primary=True,
            verified=True,
        )

        client, _ = self.complete_kakao_login(user.email, "kakao-owner")

        account = SocialAccount.objects.get(provider="kakao", uid="kakao-owner")
        user.refresh_from_db()
        self.assertEqual(account.user, user)
        self.assertTrue(user.check_password("valid-pass-123"))
        self.assertEqual(
            client.get("/_allauth/browser/v1/auth/session").status_code,
            200,
        )
        self.complete_kakao_login(user.email, "kakao-owner")
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(SocialAccount.objects.count(), 1)

    def test_verified_social_login_invalidates_unverified_claim_password(
        self,
    ) -> None:
        user = get_user_model().objects.create_user(
            "claimed@example.com",
            "attacker-known-password",
        )
        EmailAddress.objects.create(
            user=user,
            email=user.email,
            primary=True,
            verified=False,
        )

        self.complete_kakao_login(user.email, "kakao-owner")

        user.refresh_from_db()
        self.assertFalse(user.has_usable_password())
        self.assertEqual(
            SocialAccount.objects.get(provider="kakao", uid="kakao-owner").user,
            user,
        )

    def test_social_signup_blocks_duplicate_email_signup_then_allows_reset(
        self,
    ) -> None:
        social_client, _ = self.complete_kakao_login(
            "social-first@example.com",
            "social-first",
        )
        user = get_user_model().objects.get(email="social-first@example.com")
        self.assertTrue(user.username)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(
            social_client.get("/_allauth/browser/v1/auth/session").status_code,
            200,
        )

        password_client = Client(enforce_csrf_checks=True)
        response = self.post_json(
            password_client,
            "/_allauth/browser/v1/auth/signup",
            {"email": user.email, "password": "valid-pass-123"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            get_user_model().objects.filter(email=user.email).count(),
            1,
        )
        user.refresh_from_db()
        self.assertFalse(user.has_usable_password())

        self.post_json(
            password_client,
            "/_allauth/browser/v1/auth/password/request",
            {"email": user.email},
        )
        match = re.search(
            r"/auth/password/reset/([^\s/]+)",
            force_str(mail.outbox[-1].body),
        )
        assert match is not None
        self.post_json(
            password_client,
            "/_allauth/browser/v1/auth/password/reset",
            {"key": unquote(match.group(1)), "password": "valid-pass-123"},
        )

        user.refresh_from_db()
        self.assertTrue(user.check_password("valid-pass-123"))
        response = self.post_json(
            password_client,
            "/_allauth/browser/v1/auth/login",
            {"email": user.email, "password": "valid-pass-123"},
        )
        self.assertEqual(response.status_code, 200)

        relogin_client, _ = self.complete_kakao_login(user.email, "social-first")
        self.assertEqual(
            relogin_client.get("/_allauth/browser/v1/auth/session").status_code,
            200,
        )
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(SocialAccount.objects.count(), 1)
        self.assertEqual(SocialAccount.objects.get().user_id, user.pk)

    def test_new_social_login_without_verified_email_is_rejected(self) -> None:
        _, response = self.complete_kakao_login(
            None,
            "missing-email",
            email_verified=False,
        )

        self.assertIn("error=unknown", response["Location"])
        self.assertFalse(SocialAccount.objects.filter(uid="missing-email").exists())
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_new_social_login_with_unverified_email_is_rejected(self) -> None:
        client, response = self.complete_kakao_login(
            "unverified@example.com", "unverified-email", email_verified=False
        )

        self.assertIn("error=unknown", response["Location"])
        self.assertEqual(
            client.get("/_allauth/browser/v1/auth/session").status_code, 401
        )
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(SocialAccount.objects.count(), 0)

    def test_linked_kakao_relogin_without_email_reuses_user(self) -> None:
        self.complete_kakao_login("linked@example.com", "linked-owner")
        user = get_user_model().objects.get(email="linked@example.com")

        client, _ = self.complete_kakao_login(
            None, "linked-owner", email_verified=False
        )

        self.assertEqual(
            client.get("/_allauth/browser/v1/auth/session").status_code, 200
        )
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(SocialAccount.objects.count(), 1)
        self.assertEqual(SocialAccount.objects.get().user_id, user.pk)

    def complete_kakao_login(
        self,
        email: str | None,
        uid: str,
        *,
        email_verified: bool = True,
    ) -> tuple[Client, Any]:
        client = Client(enforce_csrf_checks=True)
        client.get("/_allauth/browser/v1/config")
        response = client.post(
            "/_allauth/browser/v1/auth/provider/redirect",
            {
                "provider": "kakao",
                "callback_url": "http://localhost:5173/auth/kakao/callback",
                "process": "login",
                "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
            },
        )
        query = parse_qs(urlparse(response["Location"]).query)
        self.assertIn("state", query, response["Location"])
        state = query["state"][0]

        with (
            patch.object(
                KakaoOAuth2Adapter,
                "get_access_token_data",
                return_value={"access_token": "provider-access-token"},
            ),
            patch.object(
                KakaoOAuth2Adapter,
                "complete_login",
                side_effect=partial(
                    self.build_social_login,
                    email=email,
                    uid=uid,
                    email_verified=email_verified,
                ),
            ),
        ):
            response = client.get(
                "/accounts/kakao/login/callback/",
                {"code": "authorization-code", "state": state},
            )

        self.assertEqual(response.status_code, 302)
        return client, response

    def build_social_login(
        self,
        request: HttpRequest,
        app: Any,
        token: Any,
        *,
        email: str | None,
        uid: str,
        email_verified: bool,
        **kwargs: Any,
    ) -> SocialLogin:
        provider = KakaoOAuth2Adapter(request).get_provider()
        addresses = (
            [EmailAddress(email=email, primary=True, verified=email_verified)]
            if email
            else []
        )
        return SocialLogin(
            account=SocialAccount(provider="kakao", uid=uid),
            user=get_user_model()(email=email or "", username=""),
            email_addresses=addresses,
            provider=provider,
        )

    def post_json(
        self,
        client: Client,
        path: str,
        payload: dict[str, str],
    ) -> Any:
        client.get("/_allauth/browser/v1/config")
        return client.post(
            path,
            data=json.dumps(payload),
            content_type="application/json",
            headers={"X-CSRFToken": client.cookies["csrftoken"].value},
        )
