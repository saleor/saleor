from __future__ import unicode_literals

from django.db import models
from django_images.models import Image
from django.utils.safestring import mark_safe
from django.utils.encoding import python_2_unicode_compatible

from .base_products import Product


class ImageManager(models.Manager):
    def first(self):
        return self.get_query_set()[0]


@python_2_unicode_compatible
class ProductImage(Image):
    product = models.ForeignKey(Product, related_name='images')

    objects = ImageManager()

    class Meta:
        ordering = ['id']
        app_label = 'product'

    def __str__(self):
        html = '<img src="%s" alt="">' % (
            self.get_absolute_url('admin'),)
        return mark_safe(html)
