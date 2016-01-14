from __future__ import unicode_literals

from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.encoding import python_2_unicode_compatible
from django_prices.models import PriceField
from prices import FixedDiscount, percentage_discount, Price


class NotApplicable(ValueError):
    pass


@python_2_unicode_compatible
class Discount(models.Model):
    FIXED = 'fixed'
    PERCENTAGE = 'percentage'

    DISCOUNT_TYPE_CHOICES = (
        (FIXED, pgettext_lazy('discount type', 'Fixed amount')),
        (PERCENTAGE, pgettext_lazy('discount_type', 'Percentage discount')))

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    products = models.ManyToManyField('Product', blank=True)
    categories = models.ManyToManyField('Category', blank=True)
    value = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text=pgettext_lazy('discount help',
                                'Value for a discount. It could be fixed '
                                'amount or percentage value in range 0-100'))

    class Meta:
        app_label = 'product'

    def __repr__(self):
        return 'FixedProductDiscount(name=%r, discount=%r)' % (
            str(self.discount), self.name)

    def __str__(self):
        return self.name

    def get_discount(self):
        if self.type == self.FIXED:
            discount_price = Price(net=self.value,
                                   currency=settings.DEFAULT_CURRENCY)
            return FixedDiscount(amount=discount_price, name=self.name)
        elif self.type == self.PERCENTAGE:
            return percentage_discount(value=self.value,
                                       name=self.name)
        raise NotImplementedError()

    def modifier_for_product(self, product):
        pk = product.pk
        categories = product.categories.all()
        check_price = product.get_price_per_item()
        if self.products.exists() and not (self.products.filter(pk=pk).exists()):
            raise NotApplicable('Discount not applicable for this product')
        if self.categories.exists() and not any(c in self.categories.all() for c in categories):
            raise NotApplicable('Discount not applicable for this product')
        discount = self.get_discount()
        after_discount = discount.apply(check_price)
        if after_discount.gross <= 0:
            raise NotApplicable('Discount too high for this product')
        return discount


def get_product_discounts(product, discounts, **kwargs):
    for discount in discounts:
        try:
            yield discount.modifier_for_product(product, **kwargs)
        except NotApplicable:
            pass
