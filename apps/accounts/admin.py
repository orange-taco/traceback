from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import BenefitClaim, EmailChangeRequest, SocialAccount, User, UserToken


@admin.register(User)
class UserAdmin(DjangoUserAdmin):  # type: ignore[type-arg]
    ordering = ("email",)
    list_display = ("email", "username", "is_active", "is_staff", "date_joined")
    search_fields = ("email", "username", "name", "phone_e164")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Profile",
            {
                "fields": (
                    "username",
                    "username_changed_at",
                    "name",
                    "phone_e164",
                    "phone_verified_at",
                    "email_verified_at",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined", "deleted_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff"),
            },
        ),
    )


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("user", "provider", "provider_user_id", "is_active", "linked_at")
    list_filter = ("provider", "is_active")
    search_fields = ("user__email", "provider_user_id", "provider_email")


@admin.register(EmailChangeRequest)
class EmailChangeRequestAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("user", "new_email", "expires_at", "confirmed_at", "created_at")
    search_fields = ("user__email", "new_email")


@admin.register(UserToken)
class UserTokenAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("user", "purpose", "expires_at", "consumed_at", "created_at")
    list_filter = ("purpose",)
    search_fields = ("user__email",)


@admin.register(BenefitClaim)
class BenefitClaimAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("code", "user", "claim_source", "claimed_at")
    list_filter = ("code", "claim_source")
    search_fields = ("user__email", "phone_hash", "email_hash", "social_identity_hash")
