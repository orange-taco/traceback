from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="생성 시간",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="수정 시간",
    )

    class Meta:
        abstract = True
