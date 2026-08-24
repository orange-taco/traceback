from typing import Any

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from .enums import SocialProvider
from .providers.kakao import KakaoOAuthClient
from .serializers import (
    KakaoOAuthSerializer,
    SignupSerializer,
)
from .services.social_login import complete_social_login, connect_social_account
from .tokens import issue_jwt_pair


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
        profile = KakaoOAuthClient().fetch_profile_for_code(
            code=serializer.validated_data["code"],
        )
        if request.user.is_authenticated:
            connect_social_account(
                provider=SocialProvider.KAKAO,
                profile=profile,
                user=request.user,
            )
            return Response(status=status.HTTP_204_NO_CONTENT)

        user = complete_social_login(provider=SocialProvider.KAKAO, profile=profile)
        return Response(issue_jwt_pair(user))
