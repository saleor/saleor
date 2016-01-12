from __future__ import unicode_literals

from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.encoding import python_2_unicode_compatible
from django_prices.models import PriceField
from prices import FixedDiscount, percentage_discount


class NotApplicable(ValueError):
    pass


@python_2_unicode_compatible
class FixedProductDiscount(models.Model):
    name = models.CharField(max_length=255)
    products = models.ManyToManyField('Product', blank=True)
    categories = models.ManyToManyField('Category', blank=True)
    discount = PriceField(pgettext_lazy('Discount field', 'discount value'),
                          currency=settings.DEFAULT_CURRENCY,
                          max_digits=12, decimal_places=2, null=True,
                          blank=True)
    percentage_discount = models.PositiveIntegerField(
        validators=[MaxValueValidator(100)], null=True, blank=True)

    class Meta:
        app_label = 'product'

    def __repr__(self):
        return 'FixedProductDiscount(name=%r, discount=%r)' % (
            str(self.discount), self.name)

    def __str__(self):
        return self.name

    def get_discount(self):
        if self.discount:
            return FixedDiscount(amount=self.discount, name=self.name)
        elif self.percentage_discount:
            return percentage_discount(value=self.percentage_discount,
                                       name=self.name)
        raise NotImplementedError()

    def modifier_for_product(self, variant):
        from ...product.models import ProductVariant
        if isinstance(variant, ProductVariant):
            pk = variant.product.pk
            categories = variant.product.categories.all()
        else:
            pk = variant.pk
            categories = variant.categories.all()
        check_price = variant.get_price_per_item()
        if not (self.products.filter(pk=pk).exists() and
                any(c in self.categories.all() for c in categories)):
            raise NotApplicable('Discount not applicable for this product')
        discount = self.get_discount()
        after_discount = discount.apply(check_price)
        if after_discount <= 0:
            raise NotApplicable('Discount too high for this product')
        return discount


def get_product_discounts(variant, discounts, **kwargs):
    for discount in discounts:
        try:
            yield discount.modifier_for_product(variant, **kwargs)
        except NotApplicable:
            pass
