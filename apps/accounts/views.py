from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import (
    AccountSession,
    AccountSessionSerializer,
    LoginSerializer,
    SignupSerializer,
)


class SignupView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = SignupSerializer
    response_serializer_class = AccountSessionSerializer

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        response_serializer = self.response_serializer_class(AccountSession(user))
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    response_serializer_class = AccountSessionSerializer

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.get_user()
        login(request, user)
        response_serializer = self.response_serializer_class(AccountSession(user))
        return Response(response_serializer.data)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CustomerSessionView(APIView):
    permission_classes = [AllowAny]
    response_serializer_class = AccountSessionSerializer

    def get(self, request: Request) -> Response:
        user: User | None = request.user if request.user.is_authenticated else None
        response_serializer = self.response_serializer_class(AccountSession(user))
        return Response(response_serializer.data)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminSessionStatusView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request: Request) -> Response:
        email = getattr(request.user, "email", "")
        return Response(
            {
                "email": email,
                "is_staff": request.user.is_staff,
            }
        )
