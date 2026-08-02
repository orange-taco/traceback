from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.contrib.auth import authenticate, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import User


@dataclass(frozen=True)
class AccountSession:
    user: User | None

    @property
    def authenticated(self) -> bool:
        return self.user is not None


class AccountUserSerializer(serializers.ModelSerializer[User]):
    email_verified = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "username", "email_verified")

    def get_email_verified(self, obj: User) -> bool:
        return obj.email_verified_at is not None


class AccountSessionSerializer(serializers.Serializer[AccountSession]):
    authenticated = serializers.BooleanField()
    user = AccountUserSerializer(allow_null=True)


class SignupSerializer(serializers.Serializer[User]):
    email = serializers.EmailField()
    password = serializers.CharField(
        max_length=128,
        min_length=8,
        trim_whitespace=False,
        write_only=True,
    )

    def validate_email(self, value: str) -> str:
        email = User.objects.normalize_email(value)
        email_exists = User.objects.filter(email=email).exists()
        if email_exists:
            raise serializers.ValidationError("This email is already registered.")
        return email

    def validate_password(self, value: str) -> str:
        user = User(email=self.initial_data.get("email", ""))
        try:
            password_validation.validate_password(value, user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def create(self, validated_data: dict[str, str]) -> User:
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
        )


class LoginSerializer(serializers.Serializer[dict[str, Any]]):
    default_error_messages = {
        "invalid_credentials": "Unable to sign in with the provided credentials.",
    }

    email = serializers.EmailField()
    password = serializers.CharField(
        max_length=128,
        trim_whitespace=False,
        write_only=True,
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        request = self.context.get("request")
        email = User.objects.normalize_email(attrs["email"])
        user = authenticate(
            request=request,
            username=email,
            password=attrs["password"],
        )
        if user is None or not user.is_active or user.deleted_at is not None:
            raise serializers.ValidationError(
                self.error_messages["invalid_credentials"],
                code="invalid_credentials",
            )
        attrs["email"] = email
        attrs["user"] = user
        return attrs

    def get_user(self) -> User:
        user = self.validated_data["user"]
        if not isinstance(user, User):
            raise TypeError("LoginSerializer validated data is missing a User.")
        return user
