from django.db import migrations


def move_auth_state_to_allauth(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    LegacySocialAccount = apps.get_model("accounts", "SocialAccount")
    EmailAddress = apps.get_model("account", "EmailAddress")
    SocialAccount = apps.get_model("socialaccount", "SocialAccount")

    for user in User.objects.exclude(email="").iterator():
        EmailAddress.objects.update_or_create(
            user_id=user.pk,
            email=user.email.lower(),
            defaults={
                "primary": True,
                "verified": user.email_verified_at is not None,
            },
        )

    legacy_accounts = LegacySocialAccount.objects.filter(
        is_active=True,
        deleted_at__isnull=True,
    )
    for account in legacy_accounts.iterator():
        kakao_account = {}
        if account.provider_email:
            kakao_account = {
                "email": account.provider_email,
                "is_email_verified": account.provider_email_verified,
            }
        SocialAccount.objects.update_or_create(
            provider=account.provider,
            uid=account.provider_user_id,
            defaults={
                "user_id": account.user_id,
                "extra_data": {"kakao_account": kakao_account},
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0009_emailaddress_unique_primary_email"),
        ("accounts", "0003_update_is_staff_help_text"),
        ("socialaccount", "0006_alter_socialaccount_extra_data"),
    ]

    operations = [
        migrations.RunPython(move_auth_state_to_allauth),
        migrations.RemoveIndex(
            model_name="emailchangerequest",
            name="accounts_em_user_id_96ba00_idx",
        ),
        migrations.RemoveIndex(
            model_name="emailchangerequest",
            name="accounts_em_token_h_c1c4e2_idx",
        ),
        migrations.RemoveConstraint(
            model_name="socialaccount",
            name="accounts_social_provider_identity_unique",
        ),
        migrations.RemoveConstraint(
            model_name="socialaccount",
            name="accounts_social_user_provider_unique",
        ),
        migrations.RemoveIndex(
            model_name="usertoken",
            name="accounts_us_user_id_75ce9a_idx",
        ),
        migrations.RemoveIndex(
            model_name="usertoken",
            name="accounts_us_token_h_d89c2d_idx",
        ),
        migrations.RemoveField(model_name="user", name="email_verified_at"),
        migrations.RemoveField(model_name="socialaccount", name="user"),
        migrations.RemoveField(model_name="usertoken", name="user"),
        migrations.DeleteModel(name="EmailChangeRequest"),
        migrations.DeleteModel(name="SocialAccount"),
        migrations.DeleteModel(name="UserToken"),
    ]
