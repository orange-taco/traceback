from django.urls import path
from django.urls.resolvers import URLPattern
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import SignupView

urlpatterns: list[URLPattern] = [
    path("signup", SignupView.as_view(), name="customer-signup"),
    path(
        "token/obtain",
        TokenObtainPairView.as_view(),
        name="customer-token-obtain",
    ),
    path(
        "token/refresh",
        TokenRefreshView.as_view(),
        name="customer-token-refresh",
    ),
]
