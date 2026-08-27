from __future__ import annotations

from typing import cast
from unittest import mock

from django.db import IntegrityError
from django.test import TestCase
from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.serializers import SignupSerializer


class SignupSerializerTests(TestCase):
    def test_exposes_only_email_and_write_only_password(self) -> None:
        serializer = SignupSerializer()
        password_field = cast(serializers.CharField, serializer.fields["password"])

        self.assertEqual(list(serializer.fields), ["email", "password"])
        self.assertTrue(password_field.write_only)
        self.assertFalse(password_field.trim_whitespace)

    def test_valid_signup_normalizes_email_and_creates_user(self) -> None:
        serializer = SignupSerializer(
            data={
                "email": " TEST@Example.COM ",
                "password": "StrongPass!2026",
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("StrongPass!2026"))
        self.assertNotIn("password", serializer.data)

    def test_rejects_duplicate_email_before_create(self) -> None:
        User.objects.create_user("test@example.com", "StrongPass!2026")
        serializer = SignupSerializer(
            data={
                "email": " TEST@Example.COM ",
                "password": "StrongPass!2026",
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {"email": ["This email is already registered."]},
        )

    def test_rejects_invalid_password_as_field_error(self) -> None:
        serializer = SignupSerializer(
            data={
                "email": "test@example.com",
                "password": "Short12345!",
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_create_maps_unique_race_to_email_error(self) -> None:
        serializer = SignupSerializer()

        with mock.patch.object(User.objects, "create_user", side_effect=IntegrityError):
            with self.assertRaises(serializers.ValidationError) as exc:
                serializer.create(
                    {
                        "email": "test@example.com",
                        "password": "StrongPass!2026",
                    },
                )

        self.assertEqual(
            exc.exception.detail,
            {"email": ["This email is already registered."]},
        )
