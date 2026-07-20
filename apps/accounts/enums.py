from django.db import models


class SocialProvider(models.TextChoices):
    KAKAO = "kakao", "Kakao"
    NAVER = "naver", "Naver"


class UserTokenPurpose(models.TextChoices):
    EMAIL_VERIFY = "email_verify", "Email verify"
    PASSWORD_SET = "password_set", "Password set"
    PASSWORD_RESET = "password_reset", "Password reset"


class BenefitClaimCode(models.TextChoices):
    WELCOME_SIGNUP = "welcome_signup", "Welcome signup"
