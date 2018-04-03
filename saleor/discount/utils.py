from django.conf import settings
from django.db.models import F
from django.utils.encoding import smart_text
from django.utils.translation import pgettext
from prices import Money, TaxedMoney

from . import VoucherApplyToProduct, VoucherType
from ..cart.utils import (
    get_category_variants_and_prices, get_product_variants_and_prices)
from ..core.utils import ZERO_TAXED_MONEY
from .models import NotApplicable


def increase_voucher_usage(voucher):
    """Increase voucher uses by 1."""
    voucher.used = F('used') + 1
    voucher.save(update_fields=['used'])


def decrease_voucher_usage(voucher):
    """Decrease voucher uses by 1."""
    voucher.used = F('used') - 1
    voucher.save(update_fields=['used'])


def is_category_on_sale(category, sale):
    """Check if category is descendant of one of categories on sale."""
    discounted_categories = set(sale.categories.all())
    return any([
        category.is_descendant_of(c, include_self=True)
        for c in discounted_categories])


def get_product_discount_on_sale(sale, product):
    """Return discount value if product is on sale or raise NotApplicable."""
    discounted_products = {p.pk for p in sale.products.all()}
    is_product_on_sale = (
        product.pk in discounted_products or
        is_category_on_sale(product.category, sale))
    if is_product_on_sale:
        return sale.get_discount()
    raise NotApplicable(
        pgettext(
            'Voucher not applicable',
            'Discount not applicable for this product'))


def get_product_discounts(product, discounts):
    """Return discount values for all discounts applicable to a product."""
    for discount in discounts:
        try:
            yield get_product_discount_on_sale(discount, product)
        except NotApplicable:
            pass


def calculate_discounted_price(product, price, discounts):
    """Return minimum product's price of all prices with discounts applied."""
    if discounts:
        discounts = list(get_product_discounts(product, discounts))
        if discounts:
            price = min(discount(price) for discount in discounts)
    return price


def _get_value_voucher_discount_for_checkout(voucher, checkout):
    """Calculate discount value for a voucher of value type."""
    cart_total = checkout.get_subtotal()
    voucher.validate_limit(cart_total)
    return voucher.get_discount_amount_for(cart_total)


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
    cart_total = checkout.get_subtotal()
    voucher.validate_limit(cart_total)
    return voucher.get_discount_amount_for(shipping_method.get_total_price())


def _get_product_or_category_voucher_discount_for_checkout(voucher, checkout):
    """Calculate discount value for a voucher of product or category type."""
    if voucher.type == VoucherType.PRODUCT:
        prices = [
            item[1] for item in get_product_variants_and_prices(
                checkout.cart, voucher.product)]
    else:
        prices = [
            item[1] for item in get_category_variants_and_prices(
                checkout.cart, voucher.category)]
    if not prices:
        msg = pgettext(
            'Voucher not applicable',
            'This offer is only valid for selected items.')
        raise NotApplicable(msg)
    if voucher.apply_to == VoucherApplyToProduct.ALL_PRODUCTS:
        discounts = (
            voucher.get_discount_amount_for(price) for price in prices)
        total_amount = sum(
            discounts, Money(0, settings.DEFAULT_CURRENCY))
        return total_amount
    product_total = sum(prices, ZERO_TAXED_MONEY)
    return voucher.get_discount_amount_for(product_total)


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
