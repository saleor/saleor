from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField

from .base import Product
from .variants import (ProductVariant, StockedProduct)


class PhysicalProduct(models.Model):
    weight = models.DecimalField(max_digits=6, decimal_places=2)
    price = PriceField(
        pgettext_lazy('Product field', 'price'),
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=4)

    class Meta:
        abstract = True
        app_label = 'product'

    def get_weight(self):
        try:
            return self.weight
        except AttributeError:
            return self.product.weight

    def is_available(self):
        if self.variants.exists():
            return any(variant.is_available() for variant in self)
        else:
            return False


class GenericProduct(PhysicalProduct, Product):

    class Meta:
        app_label = 'product'


class GenericVariant(ProductVariant, StockedProduct):
    product = models.ForeignKey(GenericProduct, related_name='variants')
    name = models.CharField(pgettext_lazy('Variant field', 'name'),
                            max_length=100)

    class Meta:
        app_label = 'product'
