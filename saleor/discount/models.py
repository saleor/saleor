from __future__ import unicode_literals
from datetime import date

from django.conf import settings
from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.encoding import python_2_unicode_compatible
from django_prices.models import PriceField
from prices import FixedDiscount, percentage_discount, Price


class NotApplicable(ValueError):
    pass


@python_2_unicode_compatible
class Voucher(models.Model):

    APPLY_TO_ONE_PRODUCT = 'one'
    APPLY_TO_ALL_PRODUCTS = 'all'

    DISCOUNT_VALUE_FIXED = 'fixed'
    DISCOUNT_VALUE_PERCENTAGE = 'percentage'

    DISCOUNT_VALUE_TYPE_CHOICES = (
        (DISCOUNT_VALUE_FIXED, pgettext_lazy('voucher_model', settings.DEFAULT_CURRENCY)),  # noqa
        (DISCOUNT_VALUE_PERCENTAGE, pgettext_lazy('voucher_model', '%')))

    PRODUCT_TYPE = 'product'
    CATEGORY_TYPE = 'category'
    SHIPPING_TYPE = 'shipping'
    BASKET_TYPE = 'basket'

    TYPE_CHOICES = (
        (PRODUCT_TYPE, pgettext_lazy('voucher_model', 'Product')),
        (CATEGORY_TYPE, pgettext_lazy('voucher_model', 'Category')),
        (SHIPPING_TYPE, pgettext_lazy('voucher_model', 'Shipping')),
        (BASKET_TYPE, pgettext_lazy('voucher_model', 'Baskets over'))
    )

    FIELDS_DEPENDED_ON_TYPE = ('product', 'category', 'apply_to', 'limit')

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    name = models.CharField(max_length=255, null=True, blank=True)
    code = models.CharField(max_length=12, unique=True, db_index=True)
    usage_limit = models.PositiveIntegerField(
        null=True, blank=True,
        help_text=pgettext_lazy('voucher_model', 'Unlimited if empty'))
    used = models.PositiveIntegerField(default=0, editable=False)
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(null=True, blank=True, help_text=pgettext_lazy(
        'voucher_model', 'Never expire if empty'))

    discount_value_type = models.CharField(
        max_length=10, choices=DISCOUNT_VALUE_TYPE_CHOICES, default=DISCOUNT_VALUE_FIXED)
    discount_value = models.DecimalField(max_digits=12, decimal_places=2)

    # not mandatory fields, usage depends on type
    product = models.ForeignKey('product.Product', blank=True, null=True)
    category = models.ForeignKey('product.Category', blank=True, null=True)
    apply_to = models.CharField(max_length=20, blank=True, null=True)
    limit = PriceField(max_digits=12, decimal_places=2, null=True,
                       blank=True, currency=settings.DEFAULT_CURRENCY)


    def __str__(self):
        if self.name:
            return self.name
        return self.type


@python_2_unicode_compatible
class Sale(models.Model):
    FIXED = 'fixed'
    PERCENTAGE = 'percentage'

    DISCOUNT_TYPE_CHOICES = (
        (FIXED, pgettext_lazy('discount_type', settings.DEFAULT_CURRENCY)),
        (PERCENTAGE, pgettext_lazy('discount_type', '%')))

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES,
                            default=FIXED)
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    products = models.ManyToManyField('product.Product', blank=True)
    categories = models.ManyToManyField('product.Category', blank=True)

    class Meta:
        app_label = 'discount'

    def __repr__(self):
        return 'Sale(name=%r, value=%r, type=%s)' % (
            str(self.name), self.value, self.get_type_display())

    def __str__(self):
        return self.name

    def get_discount(self):
        if self.type == self.FIXED:
            discount_price = Price(net=self.value,
                                   currency=settings.DEFAULT_CURRENCY)
            return FixedDiscount(amount=discount_price, name=self.name)
        elif self.type == self.PERCENTAGE:
            return percentage_discount(value=self.value, name=self.name)
        raise NotImplementedError('Unknown discount type')

    def _product_has_category_discount(self, product, discounted_categories):
        for category in product.categories.all():
            for discounted_category in discounted_categories:
                if category.is_descendant_of(discounted_category,
                                             include_self=True):
                    return True
        return False

    def modifier_for_variant(self, variant):
        check_price = variant.get_price_per_item()
        discounted_products = [p.pk for p in self.products.all()]
        discounted_categories = list(self.categories.all())
        if discounted_products and variant.pk not in discounted_products:
            raise NotApplicable('Discount not applicable for this product')
        if (discounted_categories and not
                self._product_has_category_discount(
                    variant.product, discounted_categories)):
            raise NotApplicable('Discount too high for this product')
        discount = self.get_discount()
        after_discount = discount.apply(check_price)
        if after_discount.gross <= 0:
            raise NotApplicable('Discount too high for this product')
        return discount


def get_variant_discounts(variant, discounts, **kwargs):
    for discount in discounts:
        try:
            yield discount.modifier_for_variant(variant, **kwargs)
        except NotApplicable:
            pass
