import os

from django.core.exceptions import ImproperlyConfigured

if not os.getenv("TRACEBACK_DATABASE_URL"):
    raise ImproperlyConfigured("TRACEBACK_DATABASE_URL must be set in production")

smtp_credentials_configured = bool(
    os.getenv("EMAIL_HOST_USER") or os.getenv("EMAIL_HOST_PASSWORD")
)
smtp_tls_enabled = os.getenv("EMAIL_USE_TLS", "false").lower() == "true"
if smtp_credentials_configured and not smtp_tls_enabled:
    raise ImproperlyConfigured(
        "EMAIL_USE_TLS=true is required when SMTP credentials are configured"
    )

from .base import *  # noqa: E402,F403

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
