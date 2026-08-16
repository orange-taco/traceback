from __future__ import annotations

import json
from typing import Any
from urllib import error, parse, request

from django.conf import settings
from rest_framework import exceptions, status

from apps.accounts.services.social_login import SocialProfile

KAKAO_AUTHORIZE_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_ME_URL = "https://kapi.kakao.com/v2/user/me"


class KakaoConfigurationError(exceptions.APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Kakao login is not configured."
    default_code = "kakao_not_configured"


class KakaoProviderError(exceptions.APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "Kakao login provider request failed."
    default_code = "kakao_provider_error"


class KakaoOAuthClient:
    def authorization_url(self, *, state: str = "") -> str:
        rest_api_key = _required_setting("KAKAO_REST_API_KEY")
        redirect_uri = _required_setting("KAKAO_REDIRECT_URI")
        query = {
            "response_type": "code",
            "client_id": rest_api_key,
            "redirect_uri": redirect_uri,
            "scope": "account_email",
        }
        if state:
            query["state"] = state
        return f"{KAKAO_AUTHORIZE_URL}?{parse.urlencode(query)}"

    def fetch_profile_for_code(self, *, code: str) -> SocialProfile:
        access_token = self._exchange_code_for_access_token(code)
        return self._fetch_profile(access_token)

    def _exchange_code_for_access_token(self, code: str) -> str:
        rest_api_key = _required_setting("KAKAO_REST_API_KEY")
        redirect_uri = _required_setting("KAKAO_REDIRECT_URI")
        payload = {
            "grant_type": "authorization_code",
            "client_id": rest_api_key,
            "redirect_uri": redirect_uri,
            "code": code,
        }
        client_secret = getattr(settings, "KAKAO_CLIENT_SECRET", "")
        if client_secret:
            payload["client_secret"] = client_secret
        response_data = _post_form(KAKAO_TOKEN_URL, payload)
        access_token = response_data.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise KakaoProviderError(
                "Kakao token response did not include access_token.",
            )
        return access_token

    def _fetch_profile(self, access_token: str) -> SocialProfile:
        response_data = _post_form(
            KAKAO_USER_ME_URL,
            {"property_keys": '["kakao_account.email"]'},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        provider_user_id = response_data.get("id")
        if provider_user_id is None:
            raise KakaoProviderError("Kakao profile response did not include id.")
        kakao_account = response_data.get("kakao_account", {})
        if not isinstance(kakao_account, dict):
            kakao_account = {}
        email = kakao_account.get("email")
        email_verified = bool(kakao_account.get("is_email_verified")) and bool(
            kakao_account.get("is_email_valid", True),
        )
        return SocialProfile(
            provider_user_id=str(provider_user_id),
            email=email if isinstance(email, str) else None,
            email_verified=email_verified,
        )


def _required_setting(name: str) -> str:
    value = getattr(settings, name, "")
    if not isinstance(value, str) or not value:
        raise KakaoConfigurationError()
    return value


def _post_form(
    url: str,
    payload: dict[str, str],
    *,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    encoded_payload = parse.urlencode(payload).encode()
    request_headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        **(headers or {}),
    }
    http_request = request.Request(
        url,
        data=encoded_payload,
        headers=request_headers,
        method="POST",
    )
    try:
        with request.urlopen(http_request, timeout=5) as response:
            response_body = response.read().decode()
    except (error.URLError, TimeoutError) as exc:
        raise KakaoProviderError() from exc
    try:
        response_data = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise KakaoProviderError("Kakao provider returned invalid JSON.") from exc
    if not isinstance(response_data, dict):
        raise KakaoProviderError("Kakao provider returned an invalid response.")
    return response_data
