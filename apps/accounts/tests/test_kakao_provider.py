from __future__ import annotations

from email.message import Message
from io import BytesIO
from typing import Any
from unittest import mock
from urllib import error

from django.test import SimpleTestCase, override_settings
from rest_framework import exceptions

from apps.accounts.providers.kakao import (
    KakaoLoginConfigurationError,
    KakaoOAuthClient,
    KakaoUpstreamError,
    _post_form_and_parse_json,
)
from apps.accounts.services.social_login import SocialUserInfo


class UrlopenResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> UrlopenResponse:
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def make_http_error(status_code: int, body: bytes) -> error.HTTPError:
    return error.HTTPError(
        "https://provider.example.com",
        status_code,
        "Provider request failed",
        hdrs=Message(),
        fp=BytesIO(body),
    )


class KakaoOAuthClientTests(SimpleTestCase):
    @override_settings(KAKAO_REST_API_KEY="", KAKAO_REDIRECT_URI="callback")
    def test_requires_rest_api_key(self) -> None:
        with self.assertRaises(KakaoLoginConfigurationError):
            KakaoOAuthClient().fetch_user_info_by_authorization_code(code="auth-code")

    @override_settings(KAKAO_REST_API_KEY="rest-key", KAKAO_REDIRECT_URI="")
    def test_requires_redirect_uri(self) -> None:
        with self.assertRaises(KakaoLoginConfigurationError):
            KakaoOAuthClient().fetch_user_info_by_authorization_code(code="auth-code")

    @override_settings(
        KAKAO_REST_API_KEY="rest-key",
        KAKAO_CLIENT_SECRET="",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_exchange_omits_client_secret_when_unset(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao._post_form_and_parse_json",
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
            KakaoOAuthClient().fetch_user_info_by_authorization_code(code="auth-code")

        token_payload = post_form.call_args_list[0].args[1]
        self.assertNotIn("client_secret", token_payload)

    @override_settings(
        KAKAO_REST_API_KEY="rest-key",
        KAKAO_CLIENT_SECRET="secret",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_fetches_user_info_by_exchanging_authorization_code(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao._post_form_and_parse_json",
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
            user_info = KakaoOAuthClient().fetch_user_info_by_authorization_code(
                code="auth-code",
            )

        self.assertEqual(
            user_info,
            SocialUserInfo(
                provider_user_id="12345",
                email="user@example.com",
                email_verified=True,
            ),
        )
        self.assertEqual(
            post_form.call_args_list[0].args[0],
            "https://kauth.kakao.com/oauth/token",
        )
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
        self.assertEqual(
            post_form.call_args_list[1].args[0],
            "https://kapi.kakao.com/v2/user/me",
        )
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
        with mock.patch(
            "apps.accounts.providers.kakao._post_form_and_parse_json", return_value={}
        ):
            with self.assertRaises(KakaoUpstreamError):
                KakaoOAuthClient().fetch_user_info_by_authorization_code(
                    code="auth-code"
                )

    @override_settings(
        KAKAO_REST_API_KEY="rest-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_rejects_user_info_response_without_id(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao._post_form_and_parse_json",
            side_effect=[
                {"access_token": "provider-token"},
                {"kakao_account": {"email": "user@example.com"}},
            ],
        ):
            with self.assertRaises(KakaoUpstreamError):
                KakaoOAuthClient().fetch_user_info_by_authorization_code(
                    code="auth-code"
                )

    @override_settings(
        KAKAO_REST_API_KEY="rest-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_marks_email_unverified_when_kakao_says_email_is_invalid(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao._post_form_and_parse_json",
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
            user_info = KakaoOAuthClient().fetch_user_info_by_authorization_code(
                code="auth-code",
            )

        self.assertEqual(user_info.email, "user@example.com")
        self.assertFalse(user_info.email_verified)

    @override_settings(
        KAKAO_REST_API_KEY="rest-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_marks_email_unverified_when_email_validity_is_missing(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao._post_form_and_parse_json",
            side_effect=[
                {"access_token": "provider-token"},
                {
                    "id": 12345,
                    "kakao_account": {
                        "email": "user@example.com",
                        "is_email_verified": True,
                    },
                },
            ],
        ):
            user_info = KakaoOAuthClient().fetch_user_info_by_authorization_code(
                code="auth-code",
            )

        self.assertFalse(user_info.email_verified)

    @override_settings(
        KAKAO_REST_API_KEY="rest-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_ignores_invalid_kakao_account_shape(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao._post_form_and_parse_json",
            side_effect=[
                {"access_token": "provider-token"},
                {"id": 12345, "kakao_account": "invalid"},
            ],
        ):
            user_info = KakaoOAuthClient().fetch_user_info_by_authorization_code(
                code="auth-code",
            )

        self.assertEqual(
            user_info,
            SocialUserInfo(
                provider_user_id="12345",
                email=None,
                email_verified=False,
            ),
        )

    @override_settings(
        KAKAO_REST_API_KEY="rest-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_maps_expired_authorization_code_to_bad_request(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao._post_form_and_parse_json",
            side_effect=make_http_error(400, b'{"error_code":"KOE320"}'),
        ):
            with self.assertRaises(exceptions.ValidationError) as exc:
                KakaoOAuthClient().fetch_user_info_by_authorization_code(
                    code="expired-code",
                )

        self.assertEqual(
            exc.exception.get_codes(),
            ["kakao_authorization_code_invalid"],
        )

    @override_settings(
        KAKAO_REST_API_KEY="rest-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_maps_invalid_client_secret_to_configuration_error(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao._post_form_and_parse_json",
            side_effect=make_http_error(400, b'{"error_code":"KOE010"}'),
        ):
            with self.assertRaises(KakaoLoginConfigurationError):
                KakaoOAuthClient().fetch_user_info_by_authorization_code(
                    code="auth-code",
                )

    @override_settings(
        KAKAO_REST_API_KEY="rest-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_maps_unknown_token_error_to_upstream_error(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao._post_form_and_parse_json",
            side_effect=make_http_error(500, b'{"error_code":"unknown"}'),
        ):
            with self.assertRaises(KakaoUpstreamError):
                KakaoOAuthClient().fetch_user_info_by_authorization_code(
                    code="auth-code",
                )

    @override_settings(
        KAKAO_REST_API_KEY="rest-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_maps_unreadable_token_error_to_upstream_error(self) -> None:
        for response_body in (
            b"not-json",
            b'[{"error_code":"KOE320"}]',
            b'{"error_code":320}',
        ):
            with self.subTest(response_body=response_body):
                with mock.patch(
                    "apps.accounts.providers.kakao._post_form_and_parse_json",
                    side_effect=make_http_error(400, response_body),
                ):
                    with self.assertRaises(KakaoUpstreamError):
                        KakaoOAuthClient().fetch_user_info_by_authorization_code(
                            code="auth-code",
                        )

    @override_settings(
        KAKAO_REST_API_KEY="rest-key",
        KAKAO_REDIRECT_URI="https://client.example.com/auth/kakao/callback",
    )
    def test_maps_user_info_http_error_to_upstream_error(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao._post_form_and_parse_json",
            side_effect=[
                {"access_token": "provider-token"},
                make_http_error(400, b'{"code":-1}'),
            ],
        ):
            with self.assertRaises(KakaoUpstreamError):
                KakaoOAuthClient().fetch_user_info_by_authorization_code(
                    code="auth-code",
                )


class PostFormTests(SimpleTestCase):
    def test_posts_form_payload_and_decodes_json_object(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao.request.urlopen",
            return_value=UrlopenResponse(b'{"ok": true}'),
        ) as urlopen:
            response_data = _post_form_and_parse_json(
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

    def test_maps_network_error_to_upstream_error(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao.request.urlopen",
            side_effect=error.URLError("down"),
        ):
            with self.assertRaises(KakaoUpstreamError):
                _post_form_and_parse_json(
                    "https://provider.example.com/token", {"code": "x"}
                )

    def test_propagates_http_error_for_caller_specific_mapping(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao.request.urlopen",
            side_effect=make_http_error(400, b'{"error_code":"KOE320"}'),
        ):
            with self.assertRaises(error.HTTPError):
                _post_form_and_parse_json(
                    "https://provider.example.com/token", {"code": "x"}
                )

    def test_maps_invalid_json_to_upstream_error(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao.request.urlopen",
            return_value=UrlopenResponse(b"not-json"),
        ):
            with self.assertRaises(KakaoUpstreamError):
                _post_form_and_parse_json(
                    "https://provider.example.com/token", {"code": "x"}
                )

    def test_maps_non_object_json_to_upstream_error(self) -> None:
        with mock.patch(
            "apps.accounts.providers.kakao.request.urlopen",
            return_value=UrlopenResponse(b'["invalid"]'),
        ):
            with self.assertRaises(KakaoUpstreamError):
                _post_form_and_parse_json(
                    "https://provider.example.com/token", {"code": "x"}
                )
