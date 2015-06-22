from __future__ import unicode_literals

from django.db import models

from .base import Product, ProductVariant


class GenericProduct(Product):

    class Meta:
        app_label = 'product'


class GenericVariant(ProductVariant):

    class Meta:
        app_label = 'product'
