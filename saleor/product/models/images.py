from __future__ import unicode_literals

from typing import Union

from django.db import models
from django.db.models import Max, F, QuerySet
from django.utils.translation import pgettext_lazy
from versatileimagefield.fields import VersatileImageField, PPOIField

from .base import Product


class ImageManager(models.Manager):
    def first(self):
        # type: () -> Union[None, ProductImage]
        try:
            return self.get_queryset()[0]
        except IndexError:
            pass


class ProductImage(models.Model):
    """ Product image model

    Fields:
    product -- foreign key to Product
    image -- uploaded image
    ppoi -- Primary Point of Interest
    alt -- short description
    order -- order in ProductImage queryset

    objects - instance of ImageManager
    """
    product = models.ForeignKey(
        Product, related_name='images',
        verbose_name=pgettext_lazy('Product image field', 'product'))
    image = VersatileImageField(
        upload_to='products', ppoi_field='ppoi', blank=False,
        verbose_name=pgettext_lazy('Product image field', 'image'))
    ppoi = PPOIField(verbose_name=pgettext_lazy('Product image field', 'ppoi'))
    alt = models.CharField(
        pgettext_lazy('Product image field', 'short description'),
        max_length=128, blank=True)
    order = models.PositiveIntegerField(
        pgettext_lazy('Product image field', 'order'),
        editable=False)

    objects = ImageManager()

    class Meta:
        ordering = ('order', )
        app_label = 'product'
        verbose_name = pgettext_lazy('Product image model', 'product image')
        verbose_name_plural = pgettext_lazy('Product image model', 'product images')

    def get_ordering_queryset(self):
        # type: () -> QuerySet
        """ Return product image in order"""
        return self.product.images.all()

    def save(self, *args, **kwargs):
        # type: (...) -> None
        if self.order is None:
            qs = self.get_ordering_queryset()
            existing_max = qs.aggregate(Max('order'))
            existing_max = existing_max.get('order__max')
            self.order = 0 if existing_max is None else existing_max + 1
        super(ProductImage, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # type: (...) -> None
        qs = self.get_ordering_queryset()
        qs.filter(order__gt=self.order).update(order=F('order') - 1)
        super(ProductImage, self).delete(*args, **kwargs)


class VariantImage(models.Model):
    """ Image for Product Variant e.g. photo of blue shirt

    Fields:
    variant -- foreign key to Product Variant
    image -- foreign key to Product Image
    """
    variant = models.ForeignKey(
        'ProductVariant', related_name='variant_images',
        verbose_name=pgettext_lazy('Variant image field', 'variant'))
    image = models.ForeignKey(
        ProductImage, related_name='variant_images',
        verbose_name=pgettext_lazy('Variant image field', 'image'))

    class Meta:
        verbose_name = pgettext_lazy(
            'Variant image model', 'variant image')
        verbose_name_plural = pgettext_lazy(
            'Variant image model', 'variant images')
