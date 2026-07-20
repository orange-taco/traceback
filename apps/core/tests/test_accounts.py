from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.accounts.enums import BenefitClaimCode, SocialProvider, UserTokenPurpose
from apps.accounts.models import BenefitClaim, SocialAccount, User, UserToken


class UserModelTests(TestCase):
    def test_user_manager_normalizes_email_and_generates_username(self) -> None:
        user = User.objects.create_user(" TEST@Example.COM ", "secret-pass")

        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.username.startswith("user_"))
        self.assertTrue(user.check_password("secret-pass"))

    def test_superuser_requires_staff_and_superuser_flags(self) -> None:
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                "admin@example.com",
                "secret-pass",
                is_staff=False,
            )

    def test_user_manager_runs_model_validation_before_save(self) -> None:
        with self.assertRaises(ValidationError):
            User.objects.create_user("not-an-email")

    def test_verified_phone_is_unique_for_active_non_deleted_users(self) -> None:
        verified_at = timezone.now()
        User.objects.create_user(
            "one@example.com",
            phone_e164="+821012345678",
            phone_verified_at=verified_at,
        )

        with self.assertRaises(ValidationError):
            User.objects.create_user(
                "two@example.com",
                phone_e164="+821012345678",
                phone_verified_at=verified_at,
            )


class AccountFoundationModelTests(TestCase):
    def test_social_account_constraints(self) -> None:
        user = User.objects.create_user("user@example.com")
        SocialAccount.objects.create(
            user=user,
            provider=SocialProvider.KAKAO,
            provider_user_id="kakao-1",
        )

        with self.assertRaises(IntegrityError):
            SocialAccount.objects.create(
                user=user,
                provider=SocialProvider.KAKAO,
                provider_user_id="kakao-2",
            )

    def test_user_token_lifetimes_are_decided_values(self) -> None:
        self.assertEqual(
            UserToken.lifetime_for(UserTokenPurpose.EMAIL_VERIFY),
            timedelta(hours=24),
        )
        self.assertEqual(
            UserToken.lifetime_for(UserTokenPurpose.PASSWORD_SET),
            timedelta(hours=1),
        )
        self.assertEqual(
            UserToken.lifetime_for(UserTokenPurpose.PASSWORD_RESET),
            timedelta(hours=1),
        )

    def test_welcome_benefit_requires_phone_hash(self) -> None:
        claim = BenefitClaim(
            code=BenefitClaimCode.WELCOME_SIGNUP,
            claim_source="sms",
        )

        with self.assertRaises(ValidationError):
            claim.validate_constraints()

    def test_welcome_benefit_phone_hash_is_unique(self) -> None:
        BenefitClaim.objects.create(
            code=BenefitClaimCode.WELCOME_SIGNUP,
            phone_hash="hash-1",
            claim_source="sms",
        )

        with self.assertRaises(IntegrityError):
            BenefitClaim.objects.create(
                code=BenefitClaimCode.WELCOME_SIGNUP,
                phone_hash="hash-1",
                claim_source="sms",
            )
