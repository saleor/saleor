from __future__ import unicode_literals

from django.utils.translation import pgettext_lazy
from django.utils.encoding import python_2_unicode_compatible
from django.db import models

from .base import Product
from .variants import (ProductVariant, PhysicalProduct, ColoredVariant,
                       StockedProduct)


class Bag(Product, PhysicalProduct, ColoredVariant):

    class Meta:
        app_label = 'product'


class Shirt(Product, PhysicalProduct, ColoredVariant):

    class Meta:
        app_label = 'product'


@python_2_unicode_compatible
class BagVariant(ProductVariant, StockedProduct):

    product = models.ForeignKey(Bag, related_name='variants')

    class Meta:
        app_label = 'product'

    def __str__(self):
        return '{0} {2} {3} {4}'.format(self.product.name,
                                        pgettext_lazy('Color:'),
                                        self.product.color)


@python_2_unicode_compatible
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

    def __str__(self):
        return '{0} {1} {2} {3} {4}'.format(self.product.name,
                                            pgettext_lazy('variant attribute',
                                                          'Size:'),
                                            self.get_size_display(),
                                            pgettext_lazy('variant attribute',
                                                          'Color:'),
                                            self.product.color)
