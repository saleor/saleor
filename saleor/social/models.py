from django.db import models
from django.conf import settings
from ..store.models import Store

class Social(models.Model):
    follow = models.BooleanField(default=True)
    store = models.ForeignKey(
        Store,
        related_name="socials",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        app_label = "social"
        ordering = ("pk",)
