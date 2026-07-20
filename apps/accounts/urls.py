from django.urls import path
from django.urls.resolvers import URLPattern

from .views import admin_session_status

urlpatterns: list[URLPattern] = [
    path("admin/session", admin_session_status, name="admin-session-status"),
]
