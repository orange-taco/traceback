from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount, SocialLogin
from allauth.socialaccount.providers.base import ProviderException
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.http import HttpRequest

from .providers import KakaoUnlinkError, unlink_kakao_user


class SocialAccountAdapter(DefaultSocialAccountAdapter):  # type: ignore[misc]
    def pre_social_login(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
    ) -> None:
        if sociallogin.is_existing:
            return
        if not any(address.verified for address in sociallogin.email_addresses):
            raise ProviderException("A verified provider email is required.")

    def validate_disconnect(
        self, account: SocialAccount, accounts: QuerySet[SocialAccount]
    ) -> None:
        if account.provider == "kakao":
            try:
                unlink_kakao_user(account.uid)
            except KakaoUnlinkError as exc:
                raise ValidationError(str(exc), code="provider_unavailable") from exc
