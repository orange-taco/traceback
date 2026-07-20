from django.urls import include, path
from django.urls.resolvers import URLPattern, URLResolver

urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", include("apps.console.accounts.urls")),
]
