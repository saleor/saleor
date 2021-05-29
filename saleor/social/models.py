from django.db import models
from django.conf import settings
from ..store.models import Store
from ..core.models import ModelWithMetadata
from ..core.permissions import SocialPermissions

class Social(ModelWithMetadata):
    tenant_id='store_id'
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
        ordering = ("pk",)
        app_label = "social"
        permissions = (
            (
                SocialPermissions.MANAGE_SOCIALS.codename,
                "Manage social.",
            ),
        )
