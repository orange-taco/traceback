from __future__ import annotations

import json
import uuid

from allauth.account.internal.flows.email_verification import (
    send_verification_email_to_address,
)
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model, logout
from django.contrib.sessions.models import Session
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST


@require_POST
def resend_email_verification(request: HttpRequest) -> HttpResponse:
    """Resend a link without revealing whether an account exists."""
    try:
        payload = json.loads(request.body or "{}")
    except (TypeError, ValueError):
        payload = {}

    email = payload.get("email") if isinstance(payload, dict) else None
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
            send_verification_email_to_address(request, address)

    # Keep the response identical for unknown, invalid, and pending addresses.
    return JsonResponse({"status": 200})


@require_http_methods(["DELETE"])
def delete_account(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=401)

    with transaction.atomic():
        user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
        if not user.deleted_at:
            deleted_at = timezone.now()
            deleted_id = uuid.uuid4().hex
            SocialAccount.objects.filter(user=user).delete()
            EmailAddress.objects.filter(user=user).delete()
            user.email = f"deleted-{deleted_id}@invalid.traceback"
            user.username = f"deleted_{deleted_id}"
            user.name = ""
            user.phone_e164 = None
            user.phone_verified_at = None
            user.is_active = False
            user.deleted_at = deleted_at
            user.set_unusable_password()
            user.save(
                update_fields=[
                    "email",
                    "username",
                    "name",
                    "phone_e164",
                    "phone_verified_at",
                    "is_active",
                    "deleted_at",
                    "password",
                ]
            )

        for session in Session.objects.all():
            if str(user.pk) == session.get_decoded().get("_auth_user_id"):
                session.delete()

    logout(request)
    return JsonResponse({"status": 204}, status=204)
