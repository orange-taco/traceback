from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import AccountUserSerializer, LoginSerializer, SignupSerializer


def _session_payload(user: User | None) -> dict[str, object]:
    if user is None:
        return {"authenticated": False, "user": None}
    return {
        "authenticated": True,
        "user": AccountUserSerializer(user).data,
    }


class SignupView(APIView):
    authentication_classes = []

    def post(self, request: Request) -> Response:
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        return Response(_session_payload(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = []

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        return Response(_session_payload(user))


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CustomerSessionView(APIView):
    def get(self, request: Request) -> Response:
        user = request.user
        if not user.is_authenticated:
            return Response(_session_payload(None))
        return Response(_session_payload(user))


class LogoutView(APIView):
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
