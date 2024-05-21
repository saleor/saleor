from django.conf import settings
from django.db import models
from ..core.models import ModelWithMetadata


class Vendor(ModelWithMetadata):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="vendors",
        on_delete=models.SET_NULL,
        null=True,
    )
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to="vendor_logos/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
