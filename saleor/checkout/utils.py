from django.utils.translation import pgettext

from ..cart.utils import (
    get_category_variants_and_prices, get_product_variants_and_prices)
from ..discount import VoucherType
from ..discount.models import NotApplicable
from ..discount.utils import (
    get_product_or_category_voucher_discount, get_shipping_voucher_discount,
    get_value_voucher_discount)


def _get_value_voucher_discount_for_checkout(voucher, checkout):
    """Calculate discount value for a voucher of value type."""
    return get_value_voucher_discount(voucher, checkout.get_subtotal())


def _get_shipping_voucher_discount_for_checkout(voucher, checkout):
    """Calculate discount value for a voucher of shipping type."""
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
    not_valid_for_country = (
        voucher.apply_to and shipping_method.country_code != voucher.apply_to)
    if not_valid_for_country:
        msg = pgettext(
            'Voucher not applicable',
            'This offer is only valid in %(country)s.')
        raise NotApplicable(
            msg % {'country': voucher.get_apply_to_display()})
    return get_shipping_voucher_discount(
        voucher, checkout.get_subtotal(), shipping_method.get_total_price())


def _get_product_or_category_voucher_discount_for_checkout(voucher, checkout):
    """Calculate discount value for a voucher of product or category type."""
    if voucher.type == VoucherType.PRODUCT:
        prices = [
            variant_price for _, variant_price in
            get_product_variants_and_prices(checkout.cart, voucher.product)]
    else:
        prices = [
            variant_price for _, variant_price in
            get_category_variants_and_prices(checkout.cart, voucher.category)]
    if not prices:
        msg = pgettext(
            'Voucher not applicable',
            'This offer is only valid for selected items.')
        raise NotApplicable(msg)
    return get_product_or_category_voucher_discount(voucher, prices)


def get_voucher_discount_for_checkout(voucher, checkout):
    """Calculate discount value depending on voucher and discount types.

    Raise NotApplicable if voucher of given type cannot be applied.
    """
    if voucher.type == VoucherType.VALUE:
        return _get_value_voucher_discount_for_checkout(voucher, checkout)
    if voucher.type == VoucherType.SHIPPING:
        return _get_shipping_voucher_discount_for_checkout(voucher, checkout)
    if voucher.type in (VoucherType.PRODUCT, VoucherType.CATEGORY):
        return _get_product_or_category_voucher_discount_for_checkout(
            voucher, checkout)
    raise NotImplementedError('Unknown discount type')
