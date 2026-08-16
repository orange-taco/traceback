from __future__ import annotations

from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


def issue_jwt_pair(user: User) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }
