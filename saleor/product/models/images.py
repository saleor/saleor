from __future__ import unicode_literals

from django.db import models
from django.db.models import Max, F
from django.utils.translation import pgettext_lazy
from versatileimagefield.fields import VersatileImageField, PPOIField

from .base import Product


class ImageManager(models.Manager):
    def first(self):
        try:
            return self.get_queryset()[0]
        except IndexError:
            pass


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images')
    image = VersatileImageField(
        upload_to='products', ppoi_field='ppoi', blank=False)
    ppoi = PPOIField()
    alt = models.CharField(
        pgettext_lazy('Product image field', 'alternative text'), max_length=128, blank=True)
    order = models.PositiveIntegerField(editable=False)

    objects = ImageManager()

    class Meta:
        ordering = ['order']
        app_label = 'product'

    def get_ordering_queryset(self):
        return self.product.images.all()

    def save(self, *args, **kwargs):
        if self.order is None:
            c = self.get_ordering_queryset().aggregate(Max('order')).get('order__max')
            self.order = 0 if c is None else c + 1
        super(ProductImage, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        qs = self.get_ordering_queryset()
        qs.filter(order__gt=self.order).update(order=F('order')-1)
        super(ProductImage, self).delete(*args, **kwargs)
