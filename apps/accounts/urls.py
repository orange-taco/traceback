from django.urls import path
from django.urls.resolvers import URLPattern
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    EmailSignupView,
    KakaoOAuthView,
)

urlpatterns: list[URLPattern] = [
    path("signup", EmailSignupView.as_view(), name="customer-signup"),
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
    path(
        "social/kakao",
        KakaoOAuthView.as_view(),
        name="customer-kakao",
    ),
]
