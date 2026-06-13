from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health", include("apps.common.health_urls")),
    path("api/v1/", include("apps.common.api_urls")),
]
