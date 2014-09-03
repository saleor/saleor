from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.encoding import python_2_unicode_compatible
from django_prices.models import PriceField

from ..product.models import Product


@python_2_unicode_compatible
class Partner(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class StockRecord(models.Model):
    partner = models.ForeignKey(Partner, null=True)
    sku = models.CharField(
        pgettext_lazy('Product field', 'sku'), max_length=32, unique=True)
    in_stock = models.PositiveIntegerField()
    price = PriceField(pgettext_lazy('Product field', 'price'),
                       max_digits=12, decimal_places=4,
                       currency=settings.DEFAULT_CURRENCY)
    allow_overselling = models.BooleanField(default=False)
    product = models.ForeignKey(Product, related_name='stockrecords')

    def __str__(self):
        return self.sku
