import os
from datetime import timedelta

os.environ.setdefault(
    "DJANGO_SECRET_KEY",
    "test-only-secret-key-with-at-least-32-bytes",
)
os.environ.setdefault("TRACEBACK_DATABASE_URL", "sqlite:///:memory:")

from .base import *  # noqa: E402,F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "SIGNING_KEY": "test-only-jwt-signing-key-with-at-least-32-bytes",
}
