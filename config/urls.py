from django.urls import include, path

from apps.core.views import health_check

urlpatterns = [
    path("health", health_check),
    path("_allauth/", include("allauth.headless.urls")),
    path("accounts/", include("allauth.urls")),
]
