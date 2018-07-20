from django.conf import settings
from django.utils.translation import pgettext_lazy


class DiscountValueType:
    FIXED = 'fixed'
    PERCENTAGE = 'percentage'

    CHOICES = [
        (FIXED, pgettext_lazy(
            'Discount type', settings.DEFAULT_CURRENCY)),
        (PERCENTAGE, pgettext_lazy('Discount type', '%'))]


class VoucherType:
    PRODUCT = 'product'
    COLLECTION = 'collection'
    CATEGORY = 'category'
    SHIPPING = 'shipping'
    VALUE = 'value'

    CHOICES = [
        (VALUE, pgettext_lazy('Voucher: discount for', 'All products')),
        (PRODUCT, pgettext_lazy('Voucher: discount for', 'Specific products')),
        (COLLECTION, pgettext_lazy(
            'Voucher: discount for', 'Specific collections of products')),
        (CATEGORY, pgettext_lazy(
            'Voucher: discount for', 'Specific categories of products')),
        (SHIPPING, pgettext_lazy('Voucher: discount for', 'Shipping'))]
