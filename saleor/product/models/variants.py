from __future__ import unicode_literals
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import pgettext_lazy
from satchless.item import Item, StockedItem
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
    stock = models.IntegerField(pgettext_lazy('Product item field', 'stock'),
                                validators=[MinValueValidator(0)],
                                default=Decimal(1))

    class Meta:
        abstract = True
        app_label = 'product'

    def get_stock(self):
        return self.stock

    def is_available(self):
        return self.get_stock() > 0


@python_2_unicode_compatible
class ColoredVariant(models.Model):
    color = models.ForeignKey(Color)

    class Meta:
        abstract = True
        app_label = 'product'

    def __str__(self):
        return '%s (%s)' % (self.product.name, self.color)


@python_2_unicode_compatible
class ProductVariant(models.Model, Item):
    sku = models.CharField(
        pgettext_lazy('Product field', 'SKU'), max_length=32, unique=True)
    # override the price attribute to implement per-variant pricing
    price = None

    class Meta:
        abstract = True
        app_label = 'product'

    def __str__(self):
        return self.product.name

    def get_price_per_item(self, discounts=None, **kwargs):
        if self.price is not None:
            price = self.price
        else:
            price = self.product.price
        if discounts:
            discounts = list(get_product_discounts(self, discounts, **kwargs))
            if discounts:
                modifier = max(discounts)
                price += modifier
        return price

    def get_weight(self):
        try:
            return self.weight
        except AttributeError:
            return self.product.weight

    def get_absolute_url(self):
        slug = self.product.get_slug()
        product_id = self.product.id
        return reverse(
            'product:details', kwargs={'slug': slug, 'product_id': product_id})

    def as_data(self):
        return {
            'product_name': str(self),
            'product_id': self.product.pk,
            'variant_id': self.pk,
            'unit_price': str(self.get_price_per_item().gross)}

    def is_shipping_required(self):
        return True
