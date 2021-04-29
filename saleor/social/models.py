from django.db import models
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

    class Meta:
        app_label = "social"
        ordering = ("pk",)
