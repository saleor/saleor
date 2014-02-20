from __future__ import unicode_literals
from decimal import Decimal

from django.db import models
from django.utils.translation import pgettext_lazy
from satchless.item import Item, StockedItem
from django_prices.models import PriceField
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.encoding import python_2_unicode_compatible

from .discounts import get_product_discounts


@python_2_unicode_compatible
class Color(models.Model):
    name = models.CharField(pgettext_lazy('Color name field', 'name'),
                            max_length=100)
    color = models.CharField(pgettext_lazy('Color hex value', 'HEX value'),
                             max_length=6)

    class Meta:
        app_label = 'product'

    def __str__(self):
        return self.name


class StockedProduct(models.Model, StockedItem):
    stock = models.DecimalField(pgettext_lazy('Product item field', 'stock'),
                                max_digits=10, decimal_places=4,
                                default=Decimal(1))

    class Meta:
        abstract = True
        app_label = 'product'

    def get_stock(self):
        return self.stock


class PhysicalProduct(models.Model):
    weight = models.DecimalField(max_digits=6, decimal_places=2)
    length = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, default=0)
    width = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, default=0)
    depth = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, default=0)

    class Meta:
        abstract = True
        app_label = 'product'


class ColoredVariants(models.Model):
    color = models.ForeignKey(Color)

    class Meta:
        abstract = True
        app_label = 'product'


@python_2_unicode_compatible
class ProductVariant(models.Model, Item):
    name = models.CharField(pgettext_lazy('Product field', 'name'),
                            max_length=128, blank=True, default='')
    price = PriceField(pgettext_lazy('Product field', 'price'),
                       currency=settings.DEFAULT_CURRENCY,
                       max_digits=12, decimal_places=4)
    sku = models.CharField(
        pgettext_lazy('Product field', 'sku'), max_length=32, unique=True)

    class Meta:
        abstract = True
        app_label = 'product'

    def __str__(self):
        return self.name or self.product.name

    def get_price_per_item(self, discounted=True, **kwargs):
        price = self.price
        if discounted:
            discounts = list(get_product_discounts(self, **kwargs))
            if discounts:
                modifier = max(discounts)
                price += modifier
        return price

    def get_absolute_url(self):
        slug = self.product.get_slug()
        product_id = self.product.id
        return reverse(
            'product:details', kwargs={'slug': slug, 'product_id': product_id})