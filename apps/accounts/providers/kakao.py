from __future__ import annotations

import json
from typing import Any
from urllib import error, parse, request

from django.conf import settings
from rest_framework import exceptions, status

from apps.accounts.services.social_login import SocialUserInfo


class KakaoLoginConfigurationError(exceptions.APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Kakao login is not configured."
    default_code = "kakao_not_configured"


class KakaoUpstreamError(exceptions.APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "Kakao login service request failed."
    default_code = "kakao_upstream_error"


class KakaoOAuthClient:
    def fetch_user_info_by_authorization_code(self, *, code: str) -> SocialUserInfo:
        access_token = self._exchange_authorization_code_for_access_token(code)
        return self._fetch_user_info(access_token)

    def _exchange_authorization_code_for_access_token(self, code: str) -> str:
        rest_api_key = getattr(settings, "KAKAO_REST_API_KEY", "")
        redirect_uri = getattr(settings, "KAKAO_REDIRECT_URI", "")
        if not all(
            isinstance(value, str) and value for value in (rest_api_key, redirect_uri)
        ):
            raise KakaoLoginConfigurationError()
        payload = {
            "grant_type": "authorization_code",
            "client_id": rest_api_key,
            "redirect_uri": redirect_uri,
            "code": code,
        }
        client_secret = getattr(settings, "KAKAO_CLIENT_SECRET", "")
        if client_secret:
            payload["client_secret"] = client_secret
        try:
            response_data = _post_form_and_parse_json(
                "https://kauth.kakao.com/oauth/token",
                payload,
            )
        except error.HTTPError as exc:
            kakao_error_code = _read_kakao_error_code(exc)
            if kakao_error_code == "KOE320":
                raise exceptions.ValidationError(
                    "Kakao authorization code is invalid or expired.",
                    code="kakao_authorization_code_invalid",
                ) from exc
            if kakao_error_code in {
                "KOE009",
                "KOE010",
                "KOE101",
                "KOE114",
                "KOE126",
                "KOE127",
                "KOE303",
                "KOE310",
            }:
                raise KakaoLoginConfigurationError() from exc
            raise KakaoUpstreamError() from exc
        access_token = response_data.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise KakaoUpstreamError(
                "Kakao token response did not include access_token.",
            )
        return access_token

    def _fetch_user_info(self, access_token: str) -> SocialUserInfo:
        try:
            response_data = _post_form_and_parse_json(
                "https://kapi.kakao.com/v2/user/me",
                {"property_keys": '["kakao_account.email"]'},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except error.HTTPError as exc:
            raise KakaoUpstreamError() from exc
        provider_user_id = response_data.get("id")
        if provider_user_id is None:
            raise KakaoUpstreamError("Kakao user response did not include id.")
        kakao_account = response_data.get("kakao_account", {})
        if not isinstance(kakao_account, dict):
            kakao_account = {}
        email = kakao_account.get("email")
        email_verified = (
            kakao_account.get("is_email_verified") is True
            and kakao_account.get("is_email_valid") is True
        )
        return SocialUserInfo(
            provider_user_id=str(provider_user_id),
            email=email if isinstance(email, str) else None,
            email_verified=email_verified,
        )


def _post_form_and_parse_json(
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
    except error.HTTPError:
        raise
    except (error.URLError, TimeoutError) as exc:
        raise KakaoUpstreamError() from exc
    try:
        response_data = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise KakaoUpstreamError("Kakao returned invalid JSON.") from exc
    if not isinstance(response_data, dict):
        raise KakaoUpstreamError("Kakao returned an invalid response.")
    return response_data


def _read_kakao_error_code(http_error: error.HTTPError) -> str | None:
    try:
        response_data = json.loads(http_error.read().decode())
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(response_data, dict):
        return None
    error_code = response_data.get("error_code")
    return error_code if isinstance(error_code, str) else None
