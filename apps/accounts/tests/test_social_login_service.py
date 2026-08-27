from __future__ import annotations

from unittest import mock

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from rest_framework import exceptions

from apps.accounts.enums import SocialProvider
from apps.accounts.models import SocialAccount, User
from apps.accounts.services.social_login import (
    SocialAccountConflict,
    SocialAccountLinkingRequired,
    SocialProfile,
    complete_social_login,
    connect_social_account,
)


class CompleteSocialLoginTests(TestCase):
    def test_existing_social_account_logs_in_and_syncs_email_snapshot(self) -> None:
        user = User.objects.create_user("user@example.com", "StrongPass!2026")
        social_account = SocialAccount.objects.create(
            user=user,
            provider=SocialProvider.KAKAO,
            provider_user_id="provider-1",
            provider_email="old@example.com",
            provider_email_verified=False,
        )

        returned_user = complete_social_login(
            provider=SocialProvider.KAKAO,
            profile=SocialProfile(
                provider_user_id="provider-1",
                email=" NEW@Example.COM ",
                email_verified=True,
            ),
        )

        self.assertEqual(returned_user, user)
        social_account.refresh_from_db()
        self.assertEqual(social_account.provider_email, "new@example.com")
        self.assertTrue(social_account.provider_email_verified)

    def test_existing_social_account_rejects_inactive_or_deleted_user(self) -> None:
        inactive = User.objects.create_user(
            "inactive@example.com",
            "StrongPass!2026",
            is_active=False,
        )
        deleted = User.objects.create_user(
            "deleted@example.com",
            "StrongPass!2026",
            deleted_at=timezone.now(),
        )
        SocialAccount.objects.create(
            user=inactive,
            provider=SocialProvider.KAKAO,
            provider_user_id="inactive-provider",
        )
        SocialAccount.objects.create(
            user=deleted,
            provider=SocialProvider.NAVER,
            provider_user_id="deleted-provider",
        )

        for provider, provider_user_id in (
            (SocialProvider.KAKAO, "inactive-provider"),
            (SocialProvider.NAVER, "deleted-provider"),
        ):
            with self.subTest(provider=provider):
                with self.assertRaises(exceptions.AuthenticationFailed) as exc:
                    complete_social_login(
                        provider=provider,
                        profile=SocialProfile(
                            provider_user_id=provider_user_id,
                            email="user@example.com",
                            email_verified=True,
                        ),
                    )

                self.assertEqual(exc.exception.get_codes(), "no_active_account")

    def test_existing_social_account_does_not_require_email_on_relogin(self) -> None:
        user = User.objects.create_user("user@example.com", "StrongPass!2026")
        SocialAccount.objects.create(
            user=user,
            provider=SocialProvider.KAKAO,
            provider_user_id="provider-1",
            provider_email="user@example.com",
            provider_email_verified=True,
        )

        returned_user = complete_social_login(
            provider=SocialProvider.KAKAO,
            profile=SocialProfile(
                provider_user_id="provider-1",
                email=None,
                email_verified=False,
            ),
        )

        self.assertEqual(returned_user, user)

    def test_requires_verified_provider_email_when_linking_is_needed(self) -> None:
        for profile, expected_code in (
            (
                SocialProfile(
                    provider_user_id="missing-email",
                    email=None,
                    email_verified=False,
                ),
                "provider_email_required",
            ),
            (
                SocialProfile(
                    provider_user_id="unverified-email",
                    email="user@example.com",
                    email_verified=False,
                ),
                "provider_email_unverified",
            ),
        ):
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(exceptions.ValidationError) as exc:
                    complete_social_login(
                        provider=SocialProvider.KAKAO,
                        profile=profile,
                    )

                self.assertEqual(exc.exception.get_codes(), [expected_code])

    def test_verified_existing_email_user_is_auto_linked(self) -> None:
        user = User.objects.create_user(
            "user@example.com",
            "StrongPass!2026",
            email_verified_at=timezone.now(),
        )

        returned_user = complete_social_login(
            provider=SocialProvider.KAKAO,
            profile=SocialProfile(
                provider_user_id="provider-1",
                email=" USER@Example.COM ",
                email_verified=True,
            ),
        )

        self.assertEqual(returned_user, user)
        self.assertTrue(
            SocialAccount.objects.filter(
                user=user,
                provider=SocialProvider.KAKAO,
                provider_user_id="provider-1",
            ).exists(),
        )

    def test_unverified_existing_email_user_requires_manual_linking(self) -> None:
        User.objects.create_user("user@example.com", "StrongPass!2026")

        with self.assertRaises(SocialAccountLinkingRequired) as exc:
            complete_social_login(
                provider=SocialProvider.KAKAO,
                profile=SocialProfile(
                    provider_user_id="provider-1",
                    email="user@example.com",
                    email_verified=True,
                ),
            )

        self.assertEqual(exc.exception.get_codes(), "social_account_linking_required")
        self.assertFalse(SocialAccount.objects.exists())

    def test_new_social_user_is_created_with_unusable_password(self) -> None:
        user = complete_social_login(
            provider=SocialProvider.KAKAO,
            profile=SocialProfile(
                provider_user_id="provider-1",
                email=" USER@Example.COM ",
                email_verified=True,
            ),
        )

        self.assertEqual(user.email, "user@example.com")
        self.assertFalse(user.has_usable_password())
        self.assertIsNotNone(user.email_verified_at)
        self.assertTrue(
            SocialAccount.objects.filter(
                user=user,
                provider=SocialProvider.KAKAO,
                provider_user_id="provider-1",
                provider_email="user@example.com",
                provider_email_verified=True,
            ).exists(),
        )

    def test_create_user_race_uses_verified_existing_user(self) -> None:
        original_create_user = User.objects.create_user

        def raise_after_concurrent_create(
            email: str,
            password: str | None = None,
            **extra_fields: object,
        ) -> User:
            original_create_user(email, password, **extra_fields)
            raise IntegrityError

        with mock.patch.object(
            User.objects,
            "create_user",
            side_effect=raise_after_concurrent_create,
        ):
            user = complete_social_login(
                provider=SocialProvider.KAKAO,
                profile=SocialProfile(
                    provider_user_id="provider-1",
                    email="user@example.com",
                    email_verified=True,
                ),
            )

        self.assertEqual(user.email, "user@example.com")
        self.assertTrue(SocialAccount.objects.filter(user=user).exists())

    def test_create_user_race_requires_manual_linking_for_unverified_user(self) -> None:
        original_create_user = User.objects.create_user

        def raise_after_concurrent_create(
            email: str,
            password: str | None = None,
            **extra_fields: object,
        ) -> User:
            extra_fields.pop("email_verified_at", None)
            original_create_user(email, password, **extra_fields)
            raise IntegrityError

        with mock.patch.object(
            User.objects,
            "create_user",
            side_effect=raise_after_concurrent_create,
        ):
            with self.assertRaises(SocialAccountLinkingRequired) as exc:
                complete_social_login(
                    provider=SocialProvider.KAKAO,
                    profile=SocialProfile(
                        provider_user_id="provider-1",
                        email="user@example.com",
                        email_verified=True,
                    ),
                )

        self.assertEqual(exc.exception.get_codes(), "social_account_linking_required")
        self.assertFalse(SocialAccount.objects.exists())


class ConnectSocialAccountTests(TestCase):
    def test_connect_creates_social_account_for_active_user(self) -> None:
        user = User.objects.create_user("user@example.com", "StrongPass!2026")

        social_account = connect_social_account(
            provider=SocialProvider.KAKAO,
            user=user,
            profile=SocialProfile(
                provider_user_id="provider-1",
                email=" USER@Example.COM ",
                email_verified=True,
            ),
        )

        self.assertEqual(social_account.user, user)
        self.assertEqual(social_account.provider_email, "user@example.com")
        self.assertTrue(social_account.provider_email_verified)

    def test_connect_rejects_inactive_or_deleted_user(self) -> None:
        for user in (
            User.objects.create_user(
                "inactive@example.com",
                "StrongPass!2026",
                is_active=False,
            ),
            User.objects.create_user(
                "deleted@example.com",
                "StrongPass!2026",
                deleted_at=timezone.now(),
            ),
        ):
            with self.subTest(email=user.email):
                with self.assertRaises(exceptions.AuthenticationFailed) as exc:
                    connect_social_account(
                        provider=SocialProvider.KAKAO,
                        user=user,
                        profile=SocialProfile(
                            provider_user_id=f"provider-{user.id}",
                            email=user.email,
                            email_verified=True,
                        ),
                    )

                self.assertEqual(exc.exception.get_codes(), "no_active_account")

    def test_connect_requires_verified_provider_email(self) -> None:
        user = User.objects.create_user("user@example.com", "StrongPass!2026")

        for profile, expected_code in (
            (
                SocialProfile(
                    provider_user_id="missing-email",
                    email=None,
                    email_verified=False,
                ),
                "provider_email_required",
            ),
            (
                SocialProfile(
                    provider_user_id="unverified-email",
                    email="user@example.com",
                    email_verified=False,
                ),
                "provider_email_unverified",
            ),
        ):
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(exceptions.ValidationError) as exc:
                    connect_social_account(
                        provider=SocialProvider.KAKAO,
                        user=user,
                        profile=profile,
                    )

                self.assertEqual(exc.exception.get_codes(), [expected_code])

    def test_connect_reuses_same_social_account_and_syncs_snapshot(self) -> None:
        user = User.objects.create_user("user@example.com", "StrongPass!2026")
        social_account = SocialAccount.objects.create(
            user=user,
            provider=SocialProvider.KAKAO,
            provider_user_id="provider-1",
            provider_email="old@example.com",
            provider_email_verified=False,
        )

        returned = connect_social_account(
            provider=SocialProvider.KAKAO,
            user=user,
            profile=SocialProfile(
                provider_user_id="provider-1",
                email="new@example.com",
                email_verified=True,
            ),
        )

        self.assertEqual(returned, social_account)
        social_account.refresh_from_db()
        self.assertEqual(social_account.provider_email, "new@example.com")
        self.assertTrue(social_account.provider_email_verified)

    def test_connect_rejects_social_account_linked_to_another_user(self) -> None:
        owner = User.objects.create_user("owner@example.com", "StrongPass!2026")
        connector = User.objects.create_user("connector@example.com", "StrongPass!2026")
        SocialAccount.objects.create(
            user=owner,
            provider=SocialProvider.KAKAO,
            provider_user_id="provider-1",
        )

        with self.assertRaises(SocialAccountConflict) as exc:
            connect_social_account(
                provider=SocialProvider.KAKAO,
                user=connector,
                profile=SocialProfile(
                    provider_user_id="provider-1",
                    email="connector@example.com",
                    email_verified=True,
                ),
            )

        self.assertEqual(exc.exception.get_codes(), "social_account_conflict")

    def test_connect_rejects_second_account_for_same_provider(self) -> None:
        user = User.objects.create_user("user@example.com", "StrongPass!2026")
        SocialAccount.objects.create(
            user=user,
            provider=SocialProvider.KAKAO,
            provider_user_id="provider-1",
        )

        with self.assertRaises(SocialAccountConflict) as exc:
            connect_social_account(
                provider=SocialProvider.KAKAO,
                user=user,
                profile=SocialProfile(
                    provider_user_id="provider-2",
                    email="user@example.com",
                    email_verified=True,
                ),
            )

        self.assertEqual(exc.exception.get_codes(), "social_account_conflict")

    def test_connect_maps_database_identity_race_to_conflict(self) -> None:
        owner = User.objects.create_user("owner@example.com", "StrongPass!2026")
        connector = User.objects.create_user("connector@example.com", "StrongPass!2026")
        SocialAccount.objects.create(
            user=owner,
            provider=SocialProvider.KAKAO,
            provider_user_id="provider-1",
            is_active=False,
        )

        with self.assertRaises(SocialAccountConflict) as exc:
            connect_social_account(
                provider=SocialProvider.KAKAO,
                user=connector,
                profile=SocialProfile(
                    provider_user_id="provider-1",
                    email="connector@example.com",
                    email_verified=True,
                ),
            )

        self.assertEqual(exc.exception.get_codes(), "social_account_conflict")
