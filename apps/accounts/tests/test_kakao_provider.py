from __future__ import annotations

from typing import Any
from unittest import mock
from urllib import error

from django.test import SimpleTestCase, override_settings

from apps.accounts.providers.kakao import (
    KAKAO_TOKEN_URL,
    KAKAO_USER_ME_URL,
    KakaoConfigurationError,
    KakaoOAuthClient,
    KakaoProviderError,
    _post_form,
)
from apps.accounts.services.social_login import SocialProfile


class UrlopenResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> UrlopenResponse:
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def read(self) -> bytes:
        return self.body


class KakaoOAuthClientTests(SimpleTestCase):
    @override_settings(KAKAO_REST_API_KEY="", KAKAO_REDIRECT_URI="callback")
    def test_requires_rest_api_key(self) -> None:
        with self.assertRaises(KakaoConfigurationError):
            KakaoOAuthClient().fetch_profile_for_code(code="auth-code")

    @override_settings(KAKAO_REST_API_KEY="rest-key", KAKAO_REDIRECT_URI="")
    def test_requires_redirect_uri(self) -> None:
        with self.assertRaises(KakaoConfigurationError):
            KakaoOAuthClient().fetch_profile_for_code(code="auth-code")

    @override_settings(
        KAKAO_REST_API_KEY="rest-key",
        KAKAO_CLIENT_SECRET="",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_exchange_omits_client_secret_when_unset(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao._post_form",
            side_effect=[
                {"access_token": "provider-token"},
                {
                    "id": 12345,
                    "kakao_account": {
                        "email": "user@example.com",
                        "is_email_verified": True,
                        "is_email_valid": True,
                    },
                },
            ],
        ) as post_form:
            KakaoOAuthClient().fetch_profile_for_code(code="auth-code")

        token_payload = post_form.call_args_list[0].args[1]
        self.assertNotIn("client_secret", token_payload)

    @override_settings(
        KAKAO_REST_API_KEY="rest-key",
        KAKAO_CLIENT_SECRET="secret",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_fetch_profile_exchanges_code_and_maps_profile(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao._post_form",
            side_effect=[
                {"access_token": "provider-token"},
                {
                    "id": 12345,
                    "kakao_account": {
                        "email": "user@example.com",
                        "is_email_verified": True,
                        "is_email_valid": True,
                    },
                },
            ],
        ) as post_form:
            profile = KakaoOAuthClient().fetch_profile_for_code(code="auth-code")

        self.assertEqual(
            profile,
            SocialProfile(
                provider_user_id="12345",
                email="user@example.com",
                email_verified=True,
            ),
        )
        self.assertEqual(post_form.call_args_list[0].args[0], KAKAO_TOKEN_URL)
        self.assertEqual(
            post_form.call_args_list[0].args[1],
            {
                "grant_type": "authorization_code",
                "client_id": "rest-key",
                "redirect_uri": "https://client.example.com/auth/kakao/callback",
                "code": "auth-code",
                "client_secret": "secret",
            },
        )
        self.assertEqual(post_form.call_args_list[1].args[0], KAKAO_USER_ME_URL)
        self.assertEqual(
            post_form.call_args_list[1].args[1],
            {"property_keys": '["kakao_account.email"]'},
        )
        self.assertEqual(
            post_form.call_args_list[1].kwargs["headers"],
            {"Authorization": "Bearer provider-token"},
        )

    @override_settings(
        KAKAO_REST_API_KEY="rest-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_rejects_token_response_without_access_token(self) -> None:
        with mock.patch("apps.accounts.providers.kakao._post_form", return_value={}):
            with self.assertRaises(KakaoProviderError):
                KakaoOAuthClient().fetch_profile_for_code(code="auth-code")

    @override_settings(
        KAKAO_REST_API_KEY="rest-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_rejects_profile_response_without_id(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao._post_form",
            side_effect=[
                {"access_token": "provider-token"},
                {"kakao_account": {"email": "user@example.com"}},
            ],
        ):
            with self.assertRaises(KakaoProviderError):
                KakaoOAuthClient().fetch_profile_for_code(code="auth-code")

    @override_settings(
        KAKAO_REST_API_KEY="rest-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_marks_email_unverified_when_kakao_says_email_is_invalid(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao._post_form",
            side_effect=[
                {"access_token": "provider-token"},
                {
                    "id": 12345,
                    "kakao_account": {
                        "email": "user@example.com",
                        "is_email_verified": True,
                        "is_email_valid": False,
                    },
                },
            ],
        ):
            profile = KakaoOAuthClient().fetch_profile_for_code(code="auth-code")

        self.assertEqual(profile.email, "user@example.com")
        self.assertFalse(profile.email_verified)

    @override_settings(
        KAKAO_REST_API_KEY="rest-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_ignores_invalid_kakao_account_shape(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao._post_form",
            side_effect=[
                {"access_token": "provider-token"},
                {"id": 12345, "kakao_account": "invalid"},
            ],
        ):
            profile = KakaoOAuthClient().fetch_profile_for_code(code="auth-code")

        self.assertEqual(
            profile,
            SocialProfile(
                provider_user_id="12345",
                email=None,
                email_verified=False,
            ),
        )


class PostFormTests(SimpleTestCase):
    def test_posts_form_payload_and_decodes_json_object(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao.request.urlopen",
            return_value=UrlopenResponse(b'{"ok": true}'),
        ) as urlopen:
            response_data = _post_form(
                "https://provider.example.com/token",
                {"code": "auth code"},
                headers={"Authorization": "Bearer provider-token"},
            )

        self.assertEqual(response_data, {"ok": True})
        http_request = urlopen.call_args.args[0]
        self.assertEqual(http_request.full_url, "https://provider.example.com/token")
        self.assertEqual(http_request.data, b"code=auth+code")
        self.assertEqual(
            http_request.get_header("Content-type"),
            "application/x-www-form-urlencoded;charset=utf-8",
        )
        self.assertEqual(
            http_request.get_header("Authorization"),
            "Bearer provider-token",
        )
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 5)

    def test_maps_url_errors_to_provider_error(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao.request.urlopen",
            side_effect=error.URLError("down"),
        ):
            with self.assertRaises(KakaoProviderError):
                _post_form("https://provider.example.com/token", {"code": "x"})

    def test_maps_invalid_json_to_provider_error(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao.request.urlopen",
            return_value=UrlopenResponse(b"not-json"),
        ):
            with self.assertRaises(KakaoProviderError):
                _post_form("https://provider.example.com/token", {"code": "x"})

    def test_rejects_non_object_json_response(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao.request.urlopen",
            return_value=UrlopenResponse(b'["invalid"]'),
        ):
            with self.assertRaises(KakaoProviderError):
                _post_form("https://provider.example.com/token", {"code": "x"})
