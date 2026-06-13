from django.urls import include, path
from django.urls.resolvers import URLPattern, URLResolver
from rest_framework.routers import DefaultRouter

from .views import health

router = DefaultRouter()

urlpatterns: list[URLPattern | URLResolver] = [
    path("health", health, name="health"),
    path("api/v1/", include(router.urls)),
]
