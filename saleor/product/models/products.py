from __future__ import unicode_literals

from django.utils.translation import pgettext_lazy
from django.db import models

from .base_products import Product
from .variants import (ProductVariant, PhysicalProduct, ColoredVariant,
                       StockedProduct)


class Bag(Product, PhysicalProduct, ColoredVariant):
    class Meta:
        app_label = 'product'


class Shirt(Product, PhysicalProduct, ColoredVariant):
    class Meta:
        app_label = 'product'


class BagVariant(ProductVariant, StockedProduct):
    product = models.ForeignKey(Bag, related_name='variants')

    class Meta:
        app_label = 'product'


class ShirtVariant(ProductVariant, StockedProduct):
    SIZE_CHOICES = (
        ('xs', pgettext_lazy('Variant size', 'XS')),
        ('s', pgettext_lazy('Variant size', 'S')),
        ('m', pgettext_lazy('Variant size', 'M')),
        ('l', pgettext_lazy('Variant size', 'L')),
        ('xl', pgettext_lazy('Variant size', 'XL')),
        ('xxl', pgettext_lazy('Variant size', 'XXL')))

    product = models.ForeignKey(Shirt, related_name='variants')
    size = models.CharField(choices=SIZE_CHOICES, max_length=3)

    class Meta:
        app_label = 'product'