from django.urls import path
from django.urls.resolvers import URLPattern

from .views import (
    AdminSessionStatusView,
    CustomerSessionView,
    LoginView,
    LogoutView,
    SignupView,
)

urlpatterns: list[URLPattern] = [
    path("signup", SignupView.as_view(), name="customer-signup"),
    path("login", LoginView.as_view(), name="customer-login"),
    path("session", CustomerSessionView.as_view(), name="customer-session"),
    path("logout", LogoutView.as_view(), name="customer-logout"),
    path(
        "admin/session",
        AdminSessionStatusView.as_view(),
        name="admin-session-status",
    ),
]
