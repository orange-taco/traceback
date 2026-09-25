from django.urls import include, path

urlpatterns = [
    path(
        "accounts/",
        include(("apps.accounts.urls", "accounts"), namespace="accounts"),
    ),
    path("_allauth/", include("allauth.headless.urls")),
    path("accounts/", include("allauth.urls")),
]
