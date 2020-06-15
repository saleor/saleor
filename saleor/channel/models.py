from django.db import models

from ..core.permissions import ChannelPermission


class Channel(models.Model):
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True)
    currencyCode = models.CharField(max_length=128)

    class Meta:
        ordering = ("slug",)
        app_label = "channel"
        permissions = (
            (ChannelPermission.MANAGE_CHANNELS.codename, "Manage channels.",),
        )
