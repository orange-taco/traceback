from __future__ import annotations

import json

from allauth.account.internal.flows.email_verification import (
    send_verification_email_to_address,
)
from allauth.account.models import EmailAddress
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_POST


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
