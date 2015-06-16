from __future__ import unicode_literals
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import pgettext_lazy
from satchless.item import StockedItem

from .base import Product, ProductVariant


class PhysicalProduct(models.Model):
    weight = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        abstract = True
        app_label = 'product'

    def get_weight(self):
        try:
            return self.weight
        except AttributeError:
            return self.product.weight


class StockedProduct(models.Model, StockedItem):
    stock = models.IntegerField(pgettext_lazy('Product item field', 'stock'),
                                validators=[MinValueValidator(0)],
                                default=Decimal(1))

    class Meta:
        abstract = True
        app_label = 'product'

    def get_stock(self):
        return self.stock

    def is_item_available(self):
        return self.get_stock() > 0


class GenericProduct(StockedProduct, PhysicalProduct, Product):

    class Meta:
        app_label = 'product'


class GenericVariant(StockedProduct, ProductVariant):

    class Meta:
        app_label = 'product'
