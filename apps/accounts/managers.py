from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

from django.contrib.auth.base_user import BaseUserManager

if TYPE_CHECKING:
    from .models import User


class UserManager(BaseUserManager["User"]):
    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email: str | None) -> str:
        if email is None:
            return ""
        return email.strip().lower()

    def generate_username(self) -> str:
        from .models import User

        while True:
            username = f"user_{secrets.token_hex(4)}"
            if not User.objects.filter(username=username).exists():
                return username

    def get_by_natural_key(self, username: str | None) -> User:
        email = self.normalize_email(username)
        return self.get(email=email, deleted_at__isnull=True)

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: object,
    ) -> User:
        if not email:
            raise ValueError("The email address must be set.")

        normalized_email = self.normalize_email(email)
        extra_fields.setdefault("username", self.generate_username())
        user = self.model(email=normalized_email, **extra_fields)
        user.set_password(password)
        user.full_clean(exclude=["password"])
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: object,
    ) -> User:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)
