from __future__ import annotations

from typing import TYPE_CHECKING, cast

from allauth.account.internal.flows.email_verification import (
    send_verification_email_to_address,
)
from allauth.account.models import EmailAddress
from django.contrib.auth import logout
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .providers import KakaoUnlinkError
from .services import delete_account

if TYPE_CHECKING:
    from .models import User


class ResendEmailVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Resend a link without revealing whether an account exists."""
        payload = request.data if isinstance(request.data, dict) else {}
        email = payload.get("email")
        if isinstance(email, str):
            address = (
                EmailAddress.objects.filter(
                    email__iexact=email.strip(),
                    verified=False,
                    user__is_active=True,
                )
                .select_related("user")
                .first()
            )
            if address:
                send_verification_email_to_address(request._request, address)

        return Response({"status": 200})


class AccountDeletionView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request: Request) -> Response:
        try:
            delete_account(cast("User", request.user))
        except KakaoUnlinkError as exc:
            return Response(
                {
                    "status": 503,
                    "errors": [{"code": "provider_unavailable", "message": str(exc)}],
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        logout(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)
