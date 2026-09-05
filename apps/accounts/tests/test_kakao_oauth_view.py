from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import exceptions
from rest_framework.test import APIClient

from apps.accounts.enums import SocialProvider
from apps.accounts.models import SocialAccount
from apps.accounts.providers.kakao import KakaoUpstreamError
from apps.accounts.services.social_login import SocialUserInfo


class KakaoOAuthViewTests(TestCase):
    def setUp(self) -> None:
        self.api_client = APIClient()
        self.user_model = get_user_model()

    def test_requires_configuration(self) -> None:
        response = self.api_client.post(
            "/api/accounts/social/kakao",
            {"code": "auth-code"},
            format="json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "kakao_not_configured")

    def test_returns_bad_request_for_invalid_authorization_code(self) -> None:
        with mock.patch(
            "apps.accounts.views.KakaoOAuthClient.fetch_user_info_by_authorization_code",
            side_effect=exceptions.ValidationError(
                "Kakao authorization code is invalid or expired.",
                code="kakao_authorization_code_invalid",
            ),
        ):
            response = self.api_client.post(
                "/api/accounts/social/kakao",
                {"code": "expired-code"},
                format="json",
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid")
        self.assertEqual(
            response.json()["details"],
            {"non_field_errors": ["Kakao authorization code is invalid or expired."]},
        )

    def test_returns_bad_gateway_for_kakao_upstream_failure(self) -> None:
        with mock.patch(
            "apps.accounts.views.KakaoOAuthClient.fetch_user_info_by_authorization_code",
            side_effect=KakaoUpstreamError(),
        ):
            response = self.api_client.post(
                "/api/accounts/social/kakao",
                {"code": "auth-code"},
                format="json",
            )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["code"], "kakao_upstream_error")

    @override_settings(
        KAKAO_REST_API_KEY="test-rest-api-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_creates_social_user_and_returns_jwt_pair(self) -> None:
        with mock.patch(
            "apps.accounts.views.KakaoOAuthClient.fetch_user_info_by_authorization_code",
            return_value=SocialUserInfo(
                provider_user_id="12345",
                email=" KAKAO@Example.COM ",
                email_verified=True,
            ),
        ):
            response = self.api_client.post(
                "/api/accounts/social/kakao",
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
    def test_reuses_existing_social_account(self) -> None:
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
            "apps.accounts.views.KakaoOAuthClient.fetch_user_info_by_authorization_code",
            return_value=SocialUserInfo(
                provider_user_id="12345",
                email="kakao@example.com",
                email_verified=True,
            ),
        ):
            response = self.api_client.post(
                "/api/accounts/social/kakao",
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
    def test_links_verified_email_user(self) -> None:
        user = self.user_model.objects.create_user(
            "kakao@example.com",
            "StrongPass!2026",
            email_verified_at=timezone.now(),
        )

        with mock.patch(
            "apps.accounts.views.KakaoOAuthClient.fetch_user_info_by_authorization_code",
            return_value=SocialUserInfo(
                provider_user_id="12345",
                email="kakao@example.com",
                email_verified=True,
            ),
        ):
            response = self.api_client.post(
                "/api/accounts/social/kakao",
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
    def test_rejects_unverified_email_user_linking(self) -> None:
        self.user_model.objects.create_user(
            "kakao@example.com",
            "StrongPass!2026",
        )

        with mock.patch(
            "apps.accounts.views.KakaoOAuthClient.fetch_user_info_by_authorization_code",
            return_value=SocialUserInfo(
                provider_user_id="12345",
                email="kakao@example.com",
                email_verified=True,
            ),
        ):
            response = self.api_client.post(
                "/api/accounts/social/kakao",
                {"code": "auth-code"},
                format="json",
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "social_account_linking_required")
        self.assertEqual(
            response.json()["message"],
            "This email is already registered. "
            "Sign in with email to link the social account.",
        )
        self.assertFalse(SocialAccount.objects.exists())

    @override_settings(
        KAKAO_REST_API_KEY="test-rest-api-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_links_authenticated_user(self) -> None:
        user = self.user_model.objects.create_user(
            "kakao@example.com",
            "StrongPass!2026",
        )
        self.api_client.force_authenticate(user=user)

        with mock.patch(
            "apps.accounts.views.KakaoOAuthClient.fetch_user_info_by_authorization_code",
            return_value=SocialUserInfo(
                provider_user_id="12345",
                email="kakao@example.com",
                email_verified=True,
            ),
        ):
            response = self.api_client.post(
                "/api/accounts/social/kakao",
                {"code": "auth-code"},
                format="json",
            )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
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
    def test_rejects_social_account_linked_elsewhere(self) -> None:
        owner = self.user_model.objects.create_user(
            "owner@example.com",
            "StrongPass!2026",
        )
        connector = self.user_model.objects.create_user(
            "connector@example.com",
            "StrongPass!2026",
        )
        SocialAccount.objects.create(
            user=owner,
            provider=SocialProvider.KAKAO,
            provider_user_id="12345",
            provider_email="owner@example.com",
            provider_email_verified=True,
        )
        self.api_client.force_authenticate(user=connector)

        with mock.patch(
            "apps.accounts.views.KakaoOAuthClient.fetch_user_info_by_authorization_code",
            return_value=SocialUserInfo(
                provider_user_id="12345",
                email="connector@example.com",
                email_verified=True,
            ),
        ):
            response = self.api_client.post(
                "/api/accounts/social/kakao",
                {"code": "auth-code"},
                format="json",
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "social_account_conflict")
        self.assertEqual(SocialAccount.objects.count(), 1)

    @override_settings(
        KAKAO_REST_API_KEY="test-rest-api-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_requires_verified_provider_email(self) -> None:
        with mock.patch(
            "apps.accounts.views.KakaoOAuthClient.fetch_user_info_by_authorization_code",
            return_value=SocialUserInfo(
                provider_user_id="12345",
                email=None,
                email_verified=False,
            ),
        ):
            missing_email_response = self.api_client.post(
                "/api/accounts/social/kakao",
                {"code": "auth-code"},
                format="json",
            )

        self.assertEqual(missing_email_response.status_code, 400)
        self.assertEqual(missing_email_response.json()["code"], "invalid")
        self.assertEqual(
            missing_email_response.json()["details"],
            {"non_field_errors": ["Provider account email is required."]},
        )

        with mock.patch(
            "apps.accounts.views.KakaoOAuthClient.fetch_user_info_by_authorization_code",
            return_value=SocialUserInfo(
                provider_user_id="12345",
                email="kakao@example.com",
                email_verified=False,
            ),
        ):
            unverified_email_response = self.api_client.post(
                "/api/accounts/social/kakao",
                {"code": "auth-code"},
                format="json",
            )

        self.assertEqual(unverified_email_response.status_code, 400)
        self.assertEqual(unverified_email_response.json()["code"], "invalid")
        self.assertEqual(
            unverified_email_response.json()["details"],
            {
                "non_field_errors": [
                    "Verified provider account email is required.",
                ],
            },
        )
        self.assertFalse(SocialAccount.objects.exists())
