from django.urls import include, path

from apps.core.views import health_check

urlpatterns = [
    path("health", health_check),
    path("api/accounts/", include("apps.accounts.urls")),
]
