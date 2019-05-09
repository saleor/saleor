from django.db import models

from versatileimagefield.fields import VersatileImageField
from versatileimagefield.placeholder import OnStoragePlaceholderImage


class VersatileImagePostProcessorTestModel(models.Model):
    """A model for testing VersatileImageFields."""

    image = VersatileImageField(
        upload_to='./',
        blank=True,
        placeholder_image=OnStoragePlaceholderImage(
            path='on-storage-placeholder/placeholder.png'
        )
    )

    class Meta:
        verbose_name = 'foo'
        verbose_name_plural = 'foos'
