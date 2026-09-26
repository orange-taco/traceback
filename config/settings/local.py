from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [FRONTEND_BASE_URL]  # noqa: F405
MAILERS = {"default": {"BACKEND": "django.core.mail.backends.console.EmailBackend"}}
