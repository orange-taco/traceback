from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.providers.base import ProviderException
from django.http import HttpRequest


# allauth does not publish a py.typed marker for this adapter.
class SocialAccountAdapter(DefaultSocialAccountAdapter):  # type: ignore[misc]
    def pre_social_login(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
    ) -> None:
        super().pre_social_login(request, sociallogin)
        if sociallogin.is_existing:
            return
        if not any(address.verified for address in sociallogin.email_addresses):
            raise ProviderException("A verified provider email is required.")
