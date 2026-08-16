from typing import Any

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from .serializers import (
    JWTTokenPairSerializer,
    KakaoAuthorizationStartSerializer,
    KakaoAuthorizationURLSerializer,
    KakaoCallbackSerializer,
    SignupSerializer,
)
from .social import KakaoOAuthClient, complete_kakao_login, issue_jwt_pair


class SignupView(GenericAPIView[Any]):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = SignupSerializer

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)


class KakaoAuthorizationStartView(GenericAPIView[Any]):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = KakaoAuthorizationStartSerializer
    response_serializer_class = KakaoAuthorizationURLSerializer

    def get(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        authorization_url = KakaoOAuthClient().authorization_url(
            state=serializer.validated_data.get("state", ""),
        )
        response_serializer = self.response_serializer_class(
            {"authorization_url": authorization_url},
        )
        return Response(response_serializer.data)


class KakaoCallbackView(GenericAPIView[Any]):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = KakaoCallbackSerializer
    response_serializer_class = JWTTokenPairSerializer

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = KakaoOAuthClient().fetch_profile_for_code(
            code=serializer.validated_data["code"],
        )
        user = complete_kakao_login(profile)
        response_serializer = self.response_serializer_class(issue_jwt_pair(user))
        return Response(response_serializer.data)
