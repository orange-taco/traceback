from django.urls import include, path

from apps.accounts.headless import delete_account, resend_email_verification
from apps.core.views import health_check

urlpatterns = [
    path("health", health_check),
    path(
        "_allauth/browser/v1/auth/email/verify/resend",
        resend_email_verification,
    ),
    path("_allauth/browser/v1/account", delete_account),
    path("_allauth/", include("allauth.headless.urls")),
    path("accounts/", include("allauth.urls")),
]
