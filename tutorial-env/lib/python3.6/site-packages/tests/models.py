import os

from django.db import models

from versatileimagefield.fields import VersatileImageField, PPOIField
from versatileimagefield.placeholder import OnDiscPlaceholderImage, OnStoragePlaceholderImage


class MaybeVersatileImageModel(models.Model):
    name = models.CharField(max_length=30)
    image = VersatileImageField(upload_to='./', blank=True, null=True)


class VersatileImageTestModel(models.Model):
    """A model for testing VersatileImageFields."""

    img_type = models.CharField(max_length=5, unique=True)
    image = VersatileImageField(
        upload_to='./',
        ppoi_field='ppoi',
        width_field='width',
        height_field='height'
    )
    height = models.PositiveIntegerField('Image Height', blank=True, null=True)
    width = models.PositiveIntegerField('Image Width', blank=True, null=True)
    optional_image = VersatileImageField(
        upload_to='./',
        blank=True,
        placeholder_image=OnDiscPlaceholderImage(
            path=os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'placeholder.png'
            )
        )
    )
    optional_image_2 = VersatileImageField(
        upload_to='./',
        blank=True,
        placeholder_image=OnStoragePlaceholderImage(
            path='on-storage-placeholder/placeholder.png'
        )
    )
    optional_image_3 = VersatileImageField(upload_to='./', blank=True)
    ppoi = PPOIField()


class VersatileImageTestUploadDirectoryModel(models.Model):
    image = VersatileImageField(upload_to='./foo/')

    class Meta:
        verbose_name = 'VIF Test Upload Dir Model'
        verbose_name_plural = 'VIF Test Upload Dir Models'


class VersatileImageWidgetTestModel(models.Model):
    """A model for testing VersatileImageField widgets."""

    image = VersatileImageField(upload_to='./', ppoi_field='ppoi')
    image_no_ppoi = VersatileImageField(upload_to='./')
    optional_image = VersatileImageField(upload_to='./', blank=True)
    optional_image_with_ppoi = VersatileImageField(
        upload_to='./',
        blank=True,
        ppoi_field='optional_image_with_ppoi_ppoi'
    )
    optional_image_2 = VersatileImageField(upload_to='./')
    required_text_field = models.CharField(max_length=20)
    ppoi = PPOIField()
    optional_image_with_ppoi_ppoi = PPOIField()
