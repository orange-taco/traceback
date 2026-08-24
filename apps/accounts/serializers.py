from __future__ import annotations

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.fields import get_error_detail

from .models import User


class SignupSerializer(serializers.ModelSerializer[User]):
    password = serializers.CharField(
        trim_whitespace=False,
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            "email",
            "password",
        ]

    def validate_email(self, value: str) -> str:
        email = User.objects.normalize_email(value)
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("This email is already registered.")
        return email

    def validate_password(self, value: str) -> str:
        initial_email = self.initial_data.get("email", "")
        user = User(email=initial_email if isinstance(initial_email, str) else "")
        try:
            password_validation.validate_password(value, user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(get_error_detail(exc)) from exc
        return value

    def create(self, validated_data: dict[str, str]) -> User:
        try:
            return User.objects.create_user(
                email=validated_data["email"],
                password=validated_data["password"],
            )
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"email": ["This email is already registered."]},
            ) from exc


class KakaoOAuthSerializer(serializers.Serializer[dict[str, str]]):
    code = serializers.CharField(
        max_length=1024,
        trim_whitespace=True,
    )
