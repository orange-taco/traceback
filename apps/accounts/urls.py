from django.urls import path
from django.urls.resolvers import URLPattern

from .views import AdminSessionStatusView

urlpatterns: list[URLPattern] = [
    path(
        "admin/session",
        AdminSessionStatusView.as_view(),
        name="admin-session-status",
    ),
]
