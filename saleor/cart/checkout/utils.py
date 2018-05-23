from datetime import date

from django.utils.translation import pgettext

from ...cart.utils import (
    get_category_variants_and_prices, get_product_variants_and_prices)
from ...discount import VoucherType
from ...discount.models import NotApplicable, Voucher
from ...discount.utils import (
    get_product_or_category_voucher_discount, get_shipping_voucher_discount,
    get_value_voucher_discount)


def save_billing_address_in_cart(cart, address):
    """Save billing address in cart if changed.

    Remove previously saved address if not connected to any user.
    """
    has_address_changed = (
        not address and cart.billing_address or
        address and not cart.billing_address or
        address and cart.billing_address and address != cart.billing_address)
    if has_address_changed:
        remove_old_address = (
            cart.billing_address and (not cart.user or (
                cart.user and
                cart.billing_address not in cart.user.addresses.all())))
        if remove_old_address:
            cart.billing_address.delete()
        cart.billing_address = address
        cart.save()


def save_shipping_address_in_cart(cart, address):
    """Save shipping address in cart if changed.

    Remove previously saved address if not connected to any user.
    """
    has_address_changed = (
        not address and cart.shipping_address or
        address and not cart.shipping_address or
        address and cart.shipping_address and address != cart.shipping_address)
    if has_address_changed:
        remove_old_address = (
            cart.shipping_address and (not cart.user or (
                cart.user and
                cart.shipping_address not in cart.user.addresses.all())))
        if remove_old_address:
            cart.shipping_address.delete()
        cart.shipping_address = address
        cart.save()


def get_checkout_data(cart, discounts, taxes):
    """Data shared between views in checkout process."""
    lines = [
        (line, line.get_total(discounts, taxes)) for line in cart.lines.all()]
    subtotal = cart.get_total(discounts, taxes)
    shipping_price = cart.get_shipping_price(taxes)
    return {
        'cart': cart,
        'cart_are_taxes_handled': bool(taxes),
        'cart_lines': lines,
        'cart_subtotal': subtotal,
        'cart_shipping_price': shipping_price}


def _get_value_voucher_discount_for_checkout(voucher, checkout):
    """Calculate discount value for a voucher of value type."""
    return get_value_voucher_discount(voucher, checkout.get_subtotal())


def _get_shipping_voucher_discount_for_checkout(voucher, checkout):
    """Calculate discount value for a voucher of shipping type."""
    if not checkout.cart.is_shipping_required():
        msg = pgettext(
            'Voucher not applicable',
            'Your order does not require shipping.')
        raise NotApplicable(msg)
    shipping_method = checkout.cart.shipping_method
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


def get_voucher_for_cart(cart, vouchers=None):
    """Return voucher with voucher code saved in cart if active or None."""
    if cart.voucher_code is not None:
        if vouchers is None:
            vouchers = Voucher.objects.active(date=date.today())
        try:
            return vouchers.get(code=cart.voucher_code)
        except Voucher.DoesNotExist:
            return None
    return None


def recalculate_cart_discount(cart, checkout):
    """Recalculate `cart.discount` based on the voucher.

    Will clear both voucher and discount if the discount is no longer
    applicable.
    """
    voucher = get_voucher_for_cart(cart)

    if voucher is not None:
        try:
            cart.discount_amount = get_voucher_discount_for_checkout(
                voucher, checkout)
            cart.discount_name = voucher.name
            cart.save()
        except NotApplicable:
            remove_discount_from_cart(cart)
    else:
        remove_discount_from_cart(cart)


def remove_discount_from_cart(cart):
    """Remove voucher data from cart."""
    cart.discount_amount = 0
    cart.discount_name = ''
    cart.voucher_code = ''
    cart.save()
