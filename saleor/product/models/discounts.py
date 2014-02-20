from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField
from prices import FixedDiscount

from base_products import Product


class NotApplicable(ValueError):
    pass


class ProductDiscountManager(models.Manager):
    def for_product(self, variant):
        # Add a caching layer here to reduce the number of queries
        return self.get_query_set().filter(products=variant.product)


class FixedProductDiscount(models.Model):
    name = models.CharField(max_length=255)
    products = models.ManyToManyField(Product, blank=True)
    discount = PriceField(pgettext_lazy('Discount field', 'discount value'),
                          currency=settings.DEFAULT_CURRENCY,
                          max_digits=12, decimal_places=4)

    objects = ProductDiscountManager()

    class Meta:
        app_label = 'product'

    def modifier_for_product(self, variant):
        if not self.products.filter(pk=variant.product.pk).exists():
            raise NotApplicable('Discount not applicable for this product')
        if self.discount > variant.get_price(discounted=False):
            raise NotApplicable('Discount too high for this product')
        return FixedDiscount(self.discount, name=self.name)

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return 'FixedProductDiscount(name=%r, discount=%r)' % (
            str(self.discount), self.name)


def get_product_discounts(variant, **kwargs):
    for discount in FixedProductDiscount.objects.for_product(variant):
        try:
            yield discount.modifier_for_product(variant, **kwargs)
        except NotApplicable:
            pass
