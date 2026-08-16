from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, parse, request

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import exceptions, status
from rest_framework_simplejwt.tokens import RefreshToken

from .enums import SocialProvider
from .models import SocialAccount, User

KAKAO_AUTHORIZE_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_ME_URL = "https://kapi.kakao.com/v2/user/me"


@dataclass(frozen=True)
class KakaoProfile:
    provider_user_id: str
    email: str | None
    email_verified: bool


class KakaoConfigurationError(exceptions.APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Kakao login is not configured."
    default_code = "kakao_not_configured"


class KakaoProviderError(exceptions.APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "Kakao login provider request failed."
    default_code = "kakao_provider_error"


class SocialLoginError(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Social login failed."
    default_code = "social_login_failed"


class SocialAccountLinkingRequired(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = (
        "Email verification is required before linking this social account."
    )
    default_code = "social_account_linking_required"


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

    def fetch_profile_for_code(self, *, code: str) -> KakaoProfile:
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

    def _fetch_profile(self, access_token: str) -> KakaoProfile:
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
        return KakaoProfile(
            provider_user_id=str(provider_user_id),
            email=email if isinstance(email, str) else None,
            email_verified=email_verified,
        )


def complete_kakao_login(profile: KakaoProfile) -> User:
    with transaction.atomic():
        social_account = (
            SocialAccount.objects.select_for_update()
            .select_related("user")
            .filter(
                provider=SocialProvider.KAKAO,
                provider_user_id=profile.provider_user_id,
                is_active=True,
                deleted_at__isnull=True,
            )
            .first()
        )
        if social_account is not None:
            user = social_account.user
            if not user.is_active or user.deleted_at is not None:
                raise exceptions.AuthenticationFailed(
                    "No active account found with the given credentials.",
                    code="no_active_account",
                )
            _sync_social_email_snapshot(social_account, profile)
            return user

        if not profile.email:
            raise SocialLoginError(
                "Kakao account email is required.",
                code="provider_email_required",
            )
        if not profile.email_verified:
            raise SocialLoginError(
                "Verified Kakao account email is required.",
                code="provider_email_unverified",
            )

        email = User.objects.normalize_email(profile.email)
        existing_user = (
            User.objects.select_for_update()
            .filter(email=email, is_active=True, deleted_at__isnull=True)
            .first()
        )
        if existing_user is not None:
            if existing_user.email_verified_at is None:
                raise SocialAccountLinkingRequired()
            user = existing_user
        else:
            user = User.objects.create_user(
                email=email,
                password=None,
                email_verified_at=timezone.now(),
            )

        _create_social_account(user, profile)
        return user


def issue_jwt_pair(user: User) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def _create_social_account(user: User, profile: KakaoProfile) -> SocialAccount:
    try:
        return SocialAccount.objects.create(
            user=user,
            provider=SocialProvider.KAKAO,
            provider_user_id=profile.provider_user_id,
            provider_email=User.objects.normalize_email(profile.email),
            provider_email_verified=profile.email_verified,
        )
    except IntegrityError as exc:
        raise SocialLoginError(
            "This Kakao account cannot be linked automatically.",
            code="social_account_conflict",
        ) from exc


def _sync_social_email_snapshot(
    social_account: SocialAccount,
    profile: KakaoProfile,
) -> None:
    provider_email = User.objects.normalize_email(profile.email)
    fields_to_update: list[str] = []
    if social_account.provider_email != provider_email:
        social_account.provider_email = provider_email
        fields_to_update.append("provider_email")
    if social_account.provider_email_verified != profile.email_verified:
        social_account.provider_email_verified = profile.email_verified
        fields_to_update.append("provider_email_verified")
    if fields_to_update:
        fields_to_update.append("updated_at")
        social_account.save(update_fields=fields_to_update)


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
