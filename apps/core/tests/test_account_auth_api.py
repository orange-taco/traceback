from unittest import mock
from urllib import parse

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.enums import SocialProvider
from apps.accounts.models import SocialAccount
from apps.accounts.social import KakaoOAuthClient, KakaoProfile


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

    @override_settings(
        KAKAO_REST_API_KEY="test-rest-api-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_kakao_start_returns_authorization_url(self) -> None:
        response = self.api_client.get(
            "/api/accounts/social/kakao/start",
            {"state": "state-123"},
        )

        self.assertEqual(response.status_code, 200)
        authorization_url = response.json()["authorization_url"]
        parsed_url = parse.urlparse(authorization_url)
        query = parse.parse_qs(parsed_url.query)
        self.assertEqual(parsed_url.scheme, "https")
        self.assertEqual(parsed_url.netloc, "kauth.kakao.com")
        self.assertEqual(parsed_url.path, "/oauth/authorize")
        self.assertEqual(query["response_type"], ["code"])
        self.assertEqual(query["client_id"], ["test-rest-api-key"])
        self.assertEqual(
            query["redirect_uri"],
            ["https://client.example.com/auth/kakao/callback"],
        )
        self.assertEqual(query["scope"], ["account_email"])
        self.assertEqual(query["state"], ["state-123"])

    def test_kakao_start_requires_configuration(self) -> None:
        response = self.api_client.get("/api/accounts/social/kakao/start")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "kakao_not_configured")

    @override_settings(
        KAKAO_REST_API_KEY="test-rest-api-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_kakao_callback_creates_social_user_and_returns_jwt_pair(self) -> None:
        with mock.patch(
            "apps.accounts.views.KakaoOAuthClient.fetch_profile_for_code",
            return_value=KakaoProfile(
                provider_user_id="12345",
                email=" KAKAO@Example.COM ",
                email_verified=True,
            ),
        ):
            response = self.api_client.post(
                "/api/accounts/social/kakao/callback",
                {"code": "auth-code"},
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())
        user = self.user_model.objects.get(email="kakao@example.com")
        self.assertFalse(user.has_usable_password())
        self.assertIsNotNone(user.email_verified_at)
        social_account = SocialAccount.objects.get(user=user)
        self.assertEqual(social_account.provider, SocialProvider.KAKAO)
        self.assertEqual(social_account.provider_user_id, "12345")
        self.assertEqual(social_account.provider_email, "kakao@example.com")
        self.assertTrue(social_account.provider_email_verified)

    @override_settings(
        KAKAO_REST_API_KEY="test-rest-api-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_kakao_callback_reuses_existing_social_account(self) -> None:
        user = self.user_model.objects.create_user(
            "kakao@example.com",
            password=None,
            email_verified_at=timezone.now(),
        )
        SocialAccount.objects.create(
            user=user,
            provider=SocialProvider.KAKAO,
            provider_user_id="12345",
            provider_email="old@example.com",
            provider_email_verified=False,
        )

        with mock.patch(
            "apps.accounts.views.KakaoOAuthClient.fetch_profile_for_code",
            return_value=KakaoProfile(
                provider_user_id="12345",
                email="kakao@example.com",
                email_verified=True,
            ),
        ):
            response = self.api_client.post(
                "/api/accounts/social/kakao/callback",
                {"code": "auth-code"},
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertEqual(SocialAccount.objects.count(), 1)
        social_account = SocialAccount.objects.get()
        self.assertEqual(social_account.provider_email, "kakao@example.com")
        self.assertTrue(social_account.provider_email_verified)

    @override_settings(
        KAKAO_REST_API_KEY="test-rest-api-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_kakao_callback_links_verified_email_user(self) -> None:
        user = self.user_model.objects.create_user(
            "kakao@example.com",
            "StrongPass!2026",
            email_verified_at=timezone.now(),
        )

        with mock.patch(
            "apps.accounts.views.KakaoOAuthClient.fetch_profile_for_code",
            return_value=KakaoProfile(
                provider_user_id="12345",
                email="kakao@example.com",
                email_verified=True,
            ),
        ):
            response = self.api_client.post(
                "/api/accounts/social/kakao/callback",
                {"code": "auth-code"},
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("refresh", response.json())
        self.assertTrue(
            SocialAccount.objects.filter(
                user=user,
                provider=SocialProvider.KAKAO,
                provider_user_id="12345",
            ).exists(),
        )

    @override_settings(
        KAKAO_REST_API_KEY="test-rest-api-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_kakao_callback_rejects_unverified_email_user_linking(self) -> None:
        self.user_model.objects.create_user(
            "kakao@example.com",
            "StrongPass!2026",
        )

        with mock.patch(
            "apps.accounts.views.KakaoOAuthClient.fetch_profile_for_code",
            return_value=KakaoProfile(
                provider_user_id="12345",
                email="kakao@example.com",
                email_verified=True,
            ),
        ):
            response = self.api_client.post(
                "/api/accounts/social/kakao/callback",
                {"code": "auth-code"},
                format="json",
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "social_account_linking_required")
        self.assertFalse(SocialAccount.objects.exists())

    @override_settings(
        KAKAO_REST_API_KEY="test-rest-api-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_kakao_callback_requires_verified_provider_email(self) -> None:
        with mock.patch(
            "apps.accounts.views.KakaoOAuthClient.fetch_profile_for_code",
            return_value=KakaoProfile(
                provider_user_id="12345",
                email=None,
                email_verified=False,
            ),
        ):
            missing_email_response = self.api_client.post(
                "/api/accounts/social/kakao/callback",
                {"code": "auth-code"},
                format="json",
            )

        self.assertEqual(missing_email_response.status_code, 400)
        self.assertEqual(
            missing_email_response.json()["code"],
            "provider_email_required",
        )

        with mock.patch(
            "apps.accounts.views.KakaoOAuthClient.fetch_profile_for_code",
            return_value=KakaoProfile(
                provider_user_id="12345",
                email="kakao@example.com",
                email_verified=False,
            ),
        ):
            unverified_email_response = self.api_client.post(
                "/api/accounts/social/kakao/callback",
                {"code": "auth-code"},
                format="json",
            )

        self.assertEqual(unverified_email_response.status_code, 400)
        self.assertEqual(
            unverified_email_response.json()["code"],
            "provider_email_unverified",
        )
        self.assertFalse(SocialAccount.objects.exists())

    @override_settings(
        KAKAO_REST_API_KEY="test-rest-api-key",
        KAKAO_CLIENT_SECRET="test-client-secret",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_kakao_oauth_client_exchanges_code_and_normalizes_profile(self) -> None:
        with mock.patch(
            "apps.accounts.social._post_form",
            side_effect=[
                {"access_token": "provider-access-token"},
                {
                    "id": 12345,
                    "kakao_account": {
                        "email": "kakao@example.com",
                        "is_email_verified": True,
                        "is_email_valid": True,
                    },
                },
            ],
        ) as post_form:
            profile = KakaoOAuthClient().fetch_profile_for_code(code="auth-code")

        self.assertEqual(
            profile,
            KakaoProfile(
                provider_user_id="12345",
                email="kakao@example.com",
                email_verified=True,
            ),
        )
        self.assertEqual(post_form.call_count, 2)
        token_call = post_form.call_args_list[0]
        self.assertEqual(token_call.args[0], "https://kauth.kakao.com/oauth/token")
        self.assertEqual(
            token_call.args[1],
            {
                "grant_type": "authorization_code",
                "client_id": "test-rest-api-key",
                "redirect_uri": "https://client.example.com/auth/kakao/callback",
                "code": "auth-code",
                "client_secret": "test-client-secret",
            },
        )
        profile_call = post_form.call_args_list[1]
        self.assertEqual(profile_call.args[0], "https://kapi.kakao.com/v2/user/me")
        self.assertEqual(
            profile_call.kwargs["headers"],
            {"Authorization": "Bearer provider-access-token"},
        )
