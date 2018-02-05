from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils.encoding import smart_text
from django.utils.translation import pgettext, pgettext_lazy
from django_countries import countries
from django_prices.models import PriceField
from django_prices.templatetags.prices_i18n import net
from prices import FixedDiscount, Price, percentage_discount

from . import DiscountValueType, VoucherApplyToProduct, VoucherType
from ..cart.utils import (
    get_category_variants_and_prices, get_product_variants_and_prices)


class NotApplicable(ValueError):
    """Exception raised when a discount is not applicable to a checkout.

    If the error is raised because the order value is too low the minimum
    price limit will be available as the `limit` attribute.
    """

    def __init__(self, msg, limit=None):
        super().__init__(msg)
        self.limit = limit


class VoucherQueryset(models.QuerySet):
    def active(self, date):
        return self.filter(
            Q(usage_limit__isnull=True) | Q(used__lt=F('usage_limit')),
            Q(end_date__isnull=True) | Q(end_date__gte=date),
            start_date__lte=date)


class Voucher(models.Model):
    type = models.CharField(
        max_length=20, choices=VoucherType.CHOICES, default=VoucherType.VALUE)
    name = models.CharField(max_length=255, null=True, blank=True)
    code = models.CharField(max_length=12, unique=True, db_index=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used = models.PositiveIntegerField(default=0, editable=False)
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(null=True, blank=True)

    discount_value_type = models.CharField(
        max_length=10, choices=DiscountValueType.CHOICES,
        default=DiscountValueType.FIXED)
    discount_value = models.DecimalField(max_digits=12, decimal_places=2)

    # not mandatory fields, usage depends on type
    product = models.ForeignKey(
        'product.Product', blank=True, null=True, on_delete=models.CASCADE)
    category = models.ForeignKey(
        'product.Category', blank=True, null=True, on_delete=models.CASCADE)
    apply_to = models.CharField(max_length=20, blank=True, null=True)
    limit = PriceField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        currency=settings.DEFAULT_CURRENCY)

    objects = VoucherQueryset.as_manager()

    @property
    def is_free(self):
        return (
            self.discount_value == Decimal(100) and
            self.discount_value_type == DiscountValueType.PERCENTAGE)

    class Meta:
        permissions = (
            ('view_voucher',
             pgettext_lazy('Permission description', 'Can view vouchers')),
            ('edit_voucher',
             pgettext_lazy('Permission description', 'Can edit vouchers')))

    def __str__(self):
        if self.name:
            return self.name
        discount = '%s %s' % (
            self.discount_value, self.get_discount_value_type_display())
        if self.type == VoucherType.SHIPPING:
            if self.is_free:
                return pgettext('Voucher type', 'Free shipping')
            return pgettext(
                'Voucher type',
                '%(discount)s off shipping') % {'discount': discount}
        if self.type == VoucherType.PRODUCT:
            return pgettext(
                'Voucher type',
                '%(discount)s off %(product)s') % {
                    'discount': discount, 'product': self.product}
        if self.type == VoucherType.CATEGORY:
            return pgettext(
                'Voucher type',
                '%(discount)s off %(category)s') % {
                    'discount': discount, 'category': self.category}
        return pgettext(
            'Voucher type', '%(discount)s off') % {'discount': discount}

    def get_apply_to_display(self):
        if self.type == VoucherType.SHIPPING and self.apply_to:
            return countries.name(self.apply_to)
        if self.type == VoucherType.SHIPPING:
            return pgettext('Voucher', 'Any country')
        if self.apply_to and self.type in {
                VoucherType.PRODUCT, VoucherType.CATEGORY}:
            choices = dict(VoucherApplyToProduct.CHOICES)
            return choices[self.apply_to]
        return None

    def get_fixed_discount_for(self, amount):
        if self.discount_value_type == DiscountValueType.FIXED:
            discount_price = Price(net=self.discount_value,
                                   currency=settings.DEFAULT_CURRENCY)
            discount = FixedDiscount(
                amount=discount_price, name=smart_text(self))
        elif self.discount_value_type == DiscountValueType.PERCENTAGE:
            discount = percentage_discount(
                value=self.discount_value, name=smart_text(self))
            fixed_discount_value = amount - discount.apply(amount)
            discount = FixedDiscount(
                amount=fixed_discount_value, name=smart_text(self))
        else:
            raise NotImplementedError('Unknown discount value type')
        if discount.amount > amount:
            return FixedDiscount(amount, name=smart_text(self))
        return discount

    def validate_limit(self, value):
        limit = self.limit if self.limit is not None else value
        if value < limit:
            msg = pgettext(
                'Voucher not applicable',
                'This offer is only valid for orders over %(amount)s.')
            raise NotApplicable(msg % {'amount': net(limit)}, limit=limit)

    def get_discount_for_checkout(self, checkout):
        if self.type == VoucherType.VALUE:
            cart_total = checkout.get_subtotal()
            self.validate_limit(cart_total)
            return self.get_fixed_discount_for(cart_total)
        if self.type == VoucherType.SHIPPING:
            if not checkout.is_shipping_required:
                msg = pgettext(
                    'Voucher not applicable',
                    'Your order does not require shipping.')
                raise NotApplicable(msg)
            shipping_method = checkout.shipping_method
            if not shipping_method:
                msg = pgettext(
                    'Voucher not applicable',
                    'Please select a shipping method first.')
                raise NotApplicable(msg)
            if (self.apply_to and
                    shipping_method.country_code != self.apply_to):
                msg = pgettext(
                    'Voucher not applicable',
                    'This offer is only valid in %(country)s.')
                raise NotApplicable(
                    msg % {'country': self.get_apply_to_display()})
            cart_total = checkout.get_subtotal()
            self.validate_limit(cart_total)
            return self.get_fixed_discount_for(shipping_method.price)
        if self.type in (VoucherType.PRODUCT, VoucherType.CATEGORY):
            if self.type == VoucherType.PRODUCT:
                prices = [
                    item[1] for item in get_product_variants_and_prices(
                        checkout.cart, self.product)]
            else:
                prices = [
                    item[1] for item in get_category_variants_and_prices(
                        checkout.cart, self.category)]
            if not prices:
                msg = pgettext(
                    'Voucher not applicable',
                    'This offer is only valid for selected items.')
                raise NotApplicable(msg)
            if self.apply_to == VoucherApplyToProduct.ALL_PRODUCTS:
                discounts = (
                    self.get_fixed_discount_for(price) for price in prices)
                discount_total = sum(
                    (discount.amount for discount in discounts),
                    Price(0, currency=settings.DEFAULT_CURRENCY))
                return FixedDiscount(discount_total, smart_text(self))
            product_total = sum(
                prices, Price(0, currency=settings.DEFAULT_CURRENCY))
            return self.get_fixed_discount_for(product_total)
        raise NotImplementedError('Unknown discount type')


class Sale(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(
        max_length=10, choices=DiscountValueType.CHOICES,
        default=DiscountValueType.FIXED)
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    products = models.ManyToManyField('product.Product', blank=True)
    categories = models.ManyToManyField('product.Category', blank=True)

    class Meta:
        app_label = 'discount'
        permissions = (
            ('view_sale',
             pgettext_lazy('Permission description', 'Can view sales')),
            ('edit_sale',
             pgettext_lazy('Permission description', 'Can edit sales')))

    def __repr__(self):
        return 'Sale(name=%r, value=%r, type=%s)' % (
            str(self.name), self.value, self.get_type_display())

    def __str__(self):
        return self.name

    def get_discount(self):
        if self.type == DiscountValueType.FIXED:
            discount_price = Price(net=self.value,
                                   currency=settings.DEFAULT_CURRENCY)
            return FixedDiscount(amount=discount_price, name=self.name)
        elif self.type == DiscountValueType.PERCENTAGE:
            return percentage_discount(value=self.value, name=self.name)
        raise NotImplementedError('Unknown discount type')

    def _product_has_category_discount(self, product, discounted_categories):
        return any([
            product.category.is_descendant_of(category, include_self=True)
            for category in discounted_categories])

    def modifier_for_product(self, product):
        discounted_products = {p.pk for p in self.products.all()}
        discounted_categories = set(self.categories.all())
        if product.pk in discounted_products:
            return self.get_discount()
        if self._product_has_category_discount(
                product, discounted_categories):
            return self.get_discount()
        raise NotApplicable(
            pgettext(
                'Voucher not applicable',
                'Discount not applicable for this product'))
