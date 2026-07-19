from django.urls import path
from django.urls.resolvers import URLPattern

from apps.accounts.views import admin_session_status

urlpatterns: list[URLPattern] = [
    path("session", admin_session_status, name="admin-session-status"),
]
