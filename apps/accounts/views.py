from typing import Any

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .enums import SocialProvider
from .providers.kakao import KakaoOAuthClient
from .serializers import (
    KakaoOAuthSerializer,
    SignupSerializer,
)
from .services.social_login import (
    get_or_create_user_for_social_login,
    link_social_account,
)


class EmailSignupView(GenericAPIView[Any]):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = SignupSerializer

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)


class KakaoOAuthView(GenericAPIView[Any]):
    permission_classes = [AllowAny]
    serializer_class = KakaoOAuthSerializer

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_info = KakaoOAuthClient().fetch_user_info_by_authorization_code(
            code=serializer.validated_data["code"],
        )
        if request.user.is_authenticated:
            link_social_account(
                provider=SocialProvider.KAKAO,
                user_info=user_info,
                user=request.user,
            )
            return Response(status=status.HTTP_204_NO_CONTENT)

        user = get_or_create_user_for_social_login(
            provider=SocialProvider.KAKAO,
            user_info=user_info,
        )
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
        )
