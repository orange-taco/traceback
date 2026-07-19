from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, ClassVar

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.common.models import TimestampedModel

from .enums import BenefitClaimCode, SocialProvider, UserTokenPurpose
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin, TimestampedModel):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=32, unique=True)
    username_changed_at = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=100, blank=True)
    phone_e164 = models.CharField(max_length=20, null=True, blank=True)  # noqa: DJ001
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["phone_e164"],
                condition=Q(phone_verified_at__isnull=False, deleted_at__isnull=True),
                name="accounts_user_verified_phone_unique",
            )
        ]

    def __str__(self) -> str:
        return self.email


class SocialAccount(TimestampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="social_accounts",
    )
    provider = models.CharField(max_length=20, choices=SocialProvider.choices)
    provider_user_id = models.CharField(max_length=255)
    provider_email = models.EmailField(null=True, blank=True)  # noqa: DJ001
    provider_email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    linked_at = models.DateTimeField(default=timezone.now)
    deleted_at = models.DateTimeField(null=True, blank=True)
    anonymized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_user_id"],
                name="accounts_social_provider_identity_unique",
            ),
            models.UniqueConstraint(
                fields=["user", "provider"],
                name="accounts_social_user_provider_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.provider}:{self.provider_user_id}"


class EmailChangeRequest(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_change_requests",
    )
    new_email = models.EmailField()
    token_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "confirmed_at", "expires_at"]),
            models.Index(fields=["token_hash"]),
        ]

    def __str__(self) -> str:
        return self.new_email

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.new_email = User.objects.normalize_email(self.new_email)
        super().save(*args, **kwargs)

    @classmethod
    def default_expires_at(cls) -> datetime:
        return timezone.now() + timedelta(hours=24)


class UserToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tokens")
    purpose = models.CharField(max_length=32, choices=UserTokenPurpose.choices)
    token_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "purpose", "consumed_at", "expires_at"]),
            models.Index(fields=["token_hash"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.purpose}"

    @classmethod
    def lifetime_for(cls, purpose: str) -> timedelta:
        if purpose == UserTokenPurpose.EMAIL_VERIFY:
            return timedelta(hours=24)
        if purpose in {
            UserTokenPurpose.PASSWORD_SET,
            UserTokenPurpose.PASSWORD_RESET,
        }:
            return timedelta(hours=1)
        raise ValueError(f"Unsupported user token purpose: {purpose}")


class BenefitClaim(models.Model):
    code = models.CharField(max_length=64, choices=BenefitClaimCode.choices)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="benefit_claims",
    )
    phone_hash = models.CharField(max_length=128, null=True, blank=True)  # noqa: DJ001
    email_hash = models.CharField(max_length=128, null=True, blank=True)  # noqa: DJ001
    social_identity_hash = models.CharField(  # noqa: DJ001
        max_length=128,
        null=True,
        blank=True,
    )
    claimed_at = models.DateTimeField(default=timezone.now)
    claim_source = models.CharField(max_length=64)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(code="welcome_signup") | Q(phone_hash__isnull=False),
                name="accounts_benefit_welcome_requires_phone_hash",
            ),
            models.UniqueConstraint(
                fields=["code", "phone_hash"],
                condition=Q(code="welcome_signup", phone_hash__isnull=False),
                name="accounts_benefit_welcome_phone_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code}:{self.claimed_at.isoformat()}"
