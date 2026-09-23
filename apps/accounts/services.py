from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.db import transaction
from django.utils import timezone

from .providers import unlink_kakao_user

if TYPE_CHECKING:
    from .models import User


def delete_account(user: User) -> None:
    """Unlink providers, then anonymize the local account and auth state."""
    social_accounts = list(SocialAccount.objects.filter(user=user))
    for account in social_accounts:
        if account.provider == "kakao":
            unlink_kakao_user(account.uid)

    with transaction.atomic():
        locked_user = get_user_model().objects.select_for_update().get(pk=user.pk)
        if not locked_user.deleted_at:
            deleted_id = uuid.uuid4().hex[:16]
            locked_user.email = f"deleted-{deleted_id}@invalid.traceback"
            locked_user.username = f"deleted_{deleted_id}"
            locked_user.name = ""
            locked_user.phone_e164 = None
            locked_user.phone_verified_at = None
            locked_user.is_active = False
            locked_user.deleted_at = timezone.now()
            locked_user.set_unusable_password()
            SocialAccount.objects.filter(user=locked_user).delete()
            EmailAddress.objects.filter(user=locked_user).delete()
            locked_user.save(
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
            if str(locked_user.pk) == session.get_decoded().get("_auth_user_id"):
                session.delete()
