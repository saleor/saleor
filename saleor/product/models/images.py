from __future__ import unicode_literals

from django.db import models
from django.utils.translation import pgettext_lazy
from versatileimagefield.fields import VersatileImageField, PPOIField

from .base import Product


class ImageManager(models.Manager):
    def first(self):
        return self.get_queryset()[0]


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images')
    image = VersatileImageField(
        upload_to='products', ppoi_field='ppoi', blank=False)
    ppoi = PPOIField()
    alt = models.CharField(
        pgettext_lazy('Product image field', 'alternative text'), max_length=128, blank=True)

    objects = ImageManager()

    class Meta:
        ordering = ['id']
        app_label = 'product'
