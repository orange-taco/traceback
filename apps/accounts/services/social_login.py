from __future__ import annotations

from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import exceptions, status

from apps.accounts.models import SocialAccount, User


@dataclass(frozen=True)
class SocialUserInfo:
    # Internal DTO normalized by provider clients before account-linking policy runs.
    # It is not a DRF serializer because it is not an HTTP request/response boundary.
    provider_user_id: str
    email: str | None
    email_verified: bool


# DRF has no built-in 409 Conflict exception. Keep these service-local instead
# of introducing a shared custom exception hierarchy before it is needed.
class SocialAccountLinkingRequired(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = (
        "This email is already registered. "
        "Sign in with email to link the social account."
    )
    default_code = "social_account_linking_required"


class SocialAccountConflict(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This social account cannot be linked automatically."
    default_code = "social_account_conflict"


def get_or_create_user_for_social_login(
    *,
    provider: str,
    user_info: SocialUserInfo,
) -> User:
    social_account = (
        SocialAccount.objects.select_related("user")
        .filter(
            provider=provider,
            provider_user_id=user_info.provider_user_id,
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
        _update_social_account_email_snapshot(social_account, user_info)
        return social_account.user

    email = _get_verified_email(user_info)
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

    _create_social_account(provider=provider, user=user, user_info=user_info)
    return user


def link_social_account(
    *,
    provider: str,
    user_info: SocialUserInfo,
    user: User,
) -> SocialAccount:
    if not user.is_active or user.deleted_at is not None:
        raise exceptions.AuthenticationFailed(
            "No active account found with the given credentials.",
            code="no_active_account",
        )

    _get_verified_email(user_info)

    social_account = SocialAccount.objects.filter(
        provider=provider,
        provider_user_id=user_info.provider_user_id,
        is_active=True,
        deleted_at__isnull=True,
    ).first()
    if social_account is not None:
        if social_account.user_id != user.id:
            raise SocialAccountConflict(
                "This social account is already linked to another user.",
            )
        _update_social_account_email_snapshot(social_account, user_info)
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
        user_info=user_info,
    )


def _get_verified_email(user_info: SocialUserInfo) -> str:
    if not user_info.email:
        raise exceptions.ValidationError(
            "Provider account email is required.",
            code="provider_email_required",
        )
    if not user_info.email_verified:
        raise exceptions.ValidationError(
            "Verified provider account email is required.",
            code="provider_email_unverified",
        )
    return User.objects.normalize_email(user_info.email)


def _create_social_account(
    *,
    provider: str,
    user: User,
    user_info: SocialUserInfo,
) -> SocialAccount:
    try:
        with transaction.atomic():
            return SocialAccount.objects.create(
                user=user,
                provider=provider,
                provider_user_id=user_info.provider_user_id,
                provider_email=User.objects.normalize_email(user_info.email),
                provider_email_verified=user_info.email_verified,
            )
    except IntegrityError as exc:
        social_account = SocialAccount.objects.filter(
            provider=provider,
            provider_user_id=user_info.provider_user_id,
            is_active=True,
            deleted_at__isnull=True,
        ).first()
        if social_account is not None and social_account.user_id == user.id:
            _update_social_account_email_snapshot(social_account, user_info)
            return social_account
        raise SocialAccountConflict() from exc


def _update_social_account_email_snapshot(
    social_account: SocialAccount,
    user_info: SocialUserInfo,
) -> None:
    if not user_info.email:
        return
    provider_email = User.objects.normalize_email(user_info.email)
    fields_to_update: list[str] = []
    if social_account.provider_email != provider_email:
        social_account.provider_email = provider_email
        fields_to_update.append("provider_email")
    if social_account.provider_email_verified != user_info.email_verified:
        social_account.provider_email_verified = user_info.email_verified
        fields_to_update.append("provider_email_verified")
    if fields_to_update:
        fields_to_update.append("updated_at")
        social_account.save(update_fields=fields_to_update)
