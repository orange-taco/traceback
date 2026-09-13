from django.db import models


class BenefitClaimCode(models.TextChoices):
    WELCOME_SIGNUP = "welcome_signup", "Welcome signup"
