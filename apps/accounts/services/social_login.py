from __future__ import annotations

from dataclasses import dataclass

from django.db import IntegrityError
from django.utils import timezone
from rest_framework import exceptions, status

from apps.accounts.models import SocialAccount, User


@dataclass(frozen=True)
class SocialProfile:
    provider_user_id: str
    email: str | None
    email_verified: bool


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


class SocialAccountConflict(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This social account cannot be linked automatically."
    default_code = "social_account_conflict"


def complete_social_login(*, provider: str, profile: SocialProfile) -> User:
    social_account = (
        SocialAccount.objects.select_related("user")
        .filter(
            provider=provider,
            provider_user_id=profile.provider_user_id,
            is_active=True,
            deleted_at__isnull=True,
        )
        .first()
    )
    if social_account is not None:
        if (
            not social_account.user.is_active
            or social_account.user.deleted_at is not None
        ):
            raise exceptions.AuthenticationFailed(
                "No active account found with the given credentials.",
                code="no_active_account",
            )
        _sync_social_email_snapshot(social_account, profile)
        return social_account.user

    email = _require_verified_provider_email(profile)
    existing_user = User.objects.filter(
        email=email,
        is_active=True,
        deleted_at__isnull=True,
    ).first()
    if existing_user is not None:
        if existing_user.email_verified_at is None:
            raise SocialAccountLinkingRequired()
        user = existing_user
    else:
        try:
            user = User.objects.create_user(
                email=email,
                password=None,
                email_verified_at=timezone.now(),
            )
        except IntegrityError:
            user = User.objects.get(
                email=email,
                is_active=True,
                deleted_at__isnull=True,
            )
            if user.email_verified_at is None:
                raise SocialAccountLinkingRequired() from None

    _create_social_account(provider=provider, user=user, profile=profile)
    return user


def connect_social_account(
    *,
    provider: str,
    profile: SocialProfile,
    user: User,
) -> SocialAccount:
    if not user.is_active or user.deleted_at is not None:
        raise exceptions.AuthenticationFailed(
            "No active account found with the given credentials.",
            code="no_active_account",
        )

    _require_verified_provider_email(profile)

    social_account = SocialAccount.objects.filter(
        provider=provider,
        provider_user_id=profile.provider_user_id,
        is_active=True,
        deleted_at__isnull=True,
    ).first()
    if social_account is not None:
        if social_account.user_id != user.id:
            raise SocialAccountConflict(
                "This social account is already linked to another user.",
            )
        _sync_social_email_snapshot(social_account, profile)
        return social_account

    provider_account = SocialAccount.objects.filter(
        user=user,
        provider=provider,
        is_active=True,
        deleted_at__isnull=True,
    ).first()
    if provider_account is not None:
        raise SocialAccountConflict(
            "This user already has a social account for this provider.",
        )

    return _create_social_account(
        provider=provider,
        user=user,
        profile=profile,
    )


def _require_verified_provider_email(profile: SocialProfile) -> str:
    if not profile.email:
        raise SocialLoginError(
            "Provider account email is required.",
            code="provider_email_required",
        )
    if not profile.email_verified:
        raise SocialLoginError(
            "Verified provider account email is required.",
            code="provider_email_unverified",
        )
    return User.objects.normalize_email(profile.email)


def _create_social_account(
    *,
    provider: str,
    user: User,
    profile: SocialProfile,
) -> SocialAccount:
    try:
        return SocialAccount.objects.create(
            user=user,
            provider=provider,
            provider_user_id=profile.provider_user_id,
            provider_email=User.objects.normalize_email(profile.email),
            provider_email_verified=profile.email_verified,
        )
    except IntegrityError as exc:
        raise SocialAccountConflict(
            "This social account cannot be linked automatically.",
        ) from exc


def _sync_social_email_snapshot(
    social_account: SocialAccount,
    profile: SocialProfile,
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
