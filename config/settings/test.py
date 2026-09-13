import os

os.environ.setdefault(
    "DJANGO_SECRET_KEY",
    "test-only-secret-key-with-at-least-32-bytes",
)
os.environ.setdefault("TRACEBACK_DATABASE_URL", "sqlite:///:memory:")

from .base import *  # noqa: E402,F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
MAILERS = {"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}}
