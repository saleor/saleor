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
    CATEGORY = 'category'
    SHIPPING = 'shipping'
    VALUE = 'value'

    CHOICES = [
        (VALUE, pgettext_lazy('Voucher: discount for', 'All purchases')),
        (PRODUCT, pgettext_lazy('Voucher: discount for', 'One product')),
        (CATEGORY, pgettext_lazy(
            'Voucher: discount for', 'A category of products')),
        (SHIPPING, pgettext_lazy('Voucher: discount for', 'Shipping'))]
