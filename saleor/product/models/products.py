from __future__ import unicode_literals

from django.db import models

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


class GenericProduct(PhysicalProduct, Product):

    class Meta:
        app_label = 'product'


class GenericVariant(PhysicalProduct, ProductVariant):

    class Meta:
        app_label = 'product'
