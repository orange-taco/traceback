from django.urls import path

from .views import AccountDeletionView, ResendEmailVerificationView

app_name = "accounts"

urlpatterns = [
    path("delete", AccountDeletionView.as_view()),
    path("email/verify/resend", ResendEmailVerificationView.as_view()),
]
