from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, ClassVar

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import TimestampedModel

from .enums import BenefitClaimCode, SocialProvider, UserTokenPurpose
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin, TimestampedModel):
    email = models.EmailField(
        help_text="로그인에 사용하는 대표 이메일",
        unique=True,
    )
    username = models.CharField(
        help_text="고객에게 노출 가능한 고유 사용자명",
        max_length=32,
        unique=True,
    )
    username_changed_at = models.DateTimeField(
        help_text="사용자명 마지막 변경 시간",
        null=True,
        blank=True,
    )
    name = models.CharField(
        help_text="고객 실명 또는 표시 이름",
        max_length=100,
        blank=True,
    )
    phone_e164 = models.CharField(  # noqa: DJ001
        help_text="SMS 인증 후 저장되는 E.164 전화번호",
        max_length=20,
        null=True,
        blank=True,
    )
    phone_verified_at = models.DateTimeField(
        help_text="전화번호 인증 완료 시간",
        null=True,
        blank=True,
    )
    email_verified_at = models.DateTimeField(
        help_text="대표 이메일 인증 완료 시간",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        help_text="로그인 가능한 활성 계정 여부",
        default=True,
    )
    is_staff = models.BooleanField(
        help_text="staff 기능 접근 여부",
        default=False,
    )
    deleted_at = models.DateTimeField(
        help_text="계정 탈퇴 또는 비활성 처리 시간",
        null=True,
        blank=True,
    )

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
        help_text="소셜 계정이 연결된 내부 사용자",
        on_delete=models.CASCADE,
        related_name="social_accounts",
    )
    provider = models.CharField(
        help_text="소셜 로그인 제공자",
        max_length=20,
        choices=SocialProvider.choices,
    )
    provider_user_id = models.CharField(
        help_text="제공자가 발급한 사용자 식별자",
        max_length=255,
    )
    provider_email = models.EmailField(  # noqa: DJ001
        help_text="제공자가 전달한 이메일 스냅샷",
        null=True,
        blank=True,
    )
    provider_email_verified = models.BooleanField(
        help_text="제공자 기준 이메일 인증 여부",
        default=False,
    )
    is_active = models.BooleanField(
        help_text="로그인 lookup에 사용할 수 있는 연결 여부",
        default=True,
    )
    linked_at = models.DateTimeField(
        help_text="소셜 계정 연결 시간",
        default=timezone.now,
    )
    deleted_at = models.DateTimeField(
        help_text="소셜 연결 해제 또는 탈퇴 처리 시간",
        null=True,
        blank=True,
    )

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
        help_text="이메일 변경을 요청한 사용자",
        on_delete=models.CASCADE,
        related_name="email_change_requests",
    )
    new_email = models.EmailField(
        help_text="변경하려는 새 대표 이메일",
    )
    token_hash = models.CharField(
        help_text="이메일 변경 확인 토큰 해시",
        max_length=128,
    )
    expires_at = models.DateTimeField(
        help_text="요청 만료 시간",
    )
    confirmed_at = models.DateTimeField(
        help_text="새 이메일 확인 완료 시간",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="요청 생성 시간",
    )

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
    user = models.ForeignKey(
        User,
        help_text="토큰이 귀속된 사용자",
        on_delete=models.CASCADE,
        related_name="tokens",
    )
    purpose = models.CharField(
        help_text="토큰 사용 목적",
        max_length=32,
        choices=UserTokenPurpose.choices,
    )
    token_hash = models.CharField(
        help_text="일회성 토큰 해시",
        max_length=128,
    )
    expires_at = models.DateTimeField(
        help_text="토큰 만료 시간",
    )
    consumed_at = models.DateTimeField(
        help_text="토큰 사용 완료 시간",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="토큰 생성 시간",
    )

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
    code = models.CharField(
        help_text="혜택 코드",
        max_length=64,
        choices=BenefitClaimCode.choices,
    )
    user = models.ForeignKey(
        User,
        help_text="혜택을 받은 사용자",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="benefit_claims",
    )
    phone_hash = models.CharField(  # noqa: DJ001
        help_text="전화번호 HMAC 해시",
        max_length=128,
        null=True,
        blank=True,
    )
    claimed_at = models.DateTimeField(
        help_text="혜택 지급 시간",
        default=timezone.now,
    )
    claim_source = models.CharField(
        help_text="혜택 지급 트리거 출처",
        max_length=64,
    )
    metadata = models.JSONField(
        help_text="혜택 지급 관련 추가 정보",
        default=dict,
        blank=True,
    )

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
