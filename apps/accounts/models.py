from __future__ import annotations

from typing import ClassVar

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import TimestampedModel

from .enums import BenefitClaimCode
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
