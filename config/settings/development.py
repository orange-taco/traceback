from .base import *  # noqa: F403

DEBUG = False

# Development is served behind Nginx with HTTPS, like the future production
# environment. Local Docker development continues to use config.settings.local.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
