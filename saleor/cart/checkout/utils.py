from datetime import date

from django.db import transaction
from django.utils.encoding import smart_text
from django.utils.translation import get_language, pgettext

from ...account.utils import store_user_address
from ...cart.utils import (
    get_category_variants_and_prices, get_product_variants_and_prices)
from ...core.utils.taxes import ZERO_MONEY, get_taxes_for_country
from ...discount import VoucherType
from ...discount.models import NotApplicable, Voucher
from ...discount.utils import (
    get_product_or_category_voucher_discount, get_shipping_voucher_discount,
    get_value_voucher_discount, increase_voucher_usage)
from ...order.models import Order
from ...order.utils import add_variant_to_order


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
    subtotal = cart.get_subtotal(discounts, taxes)
    total = cart.get_total(discounts, taxes)
    shipping_price = cart.get_shipping_price(taxes)
    return {
        'cart': cart,
        'cart_are_taxes_handled': bool(taxes),
        'cart_lines': lines,
        'cart_shipping_price': shipping_price,
        'cart_subtotal': subtotal,
        'cart_total': total}


def _get_value_voucher_discount_for_cart(voucher, cart):
    """Calculate discount value for a voucher of value type."""
    return get_value_voucher_discount(voucher, cart.get_subtotal())


def _get_shipping_voucher_discount_for_cart(voucher, cart):
    """Calculate discount value for a voucher of shipping type."""
    if not cart.is_shipping_required():
        msg = pgettext(
            'Voucher not applicable',
            'Your order does not require shipping.')
        raise NotApplicable(msg)
    shipping_method = cart.shipping_method
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
        voucher, cart.get_subtotal(), shipping_method.get_total_price())


def _get_product_or_category_voucher_discount_for_cart(voucher, cart):
    """Calculate discount value for a voucher of product or category type."""
    if voucher.type == VoucherType.PRODUCT:
        prices = [
            variant_price for _, variant_price in
            get_product_variants_and_prices(cart, voucher.product)]
    else:
        prices = [
            variant_price for _, variant_price in
            get_category_variants_and_prices(cart, voucher.category)]
    if not prices:
        msg = pgettext(
            'Voucher not applicable',
            'This offer is only valid for selected items.')
        raise NotApplicable(msg)
    return get_product_or_category_voucher_discount(voucher, prices)


def get_voucher_discount_for_cart(voucher, cart):
    """Calculate discount value depending on voucher and discount types.

    Raise NotApplicable if voucher of given type cannot be applied.
    """
    if voucher.type == VoucherType.VALUE:
        return _get_value_voucher_discount_for_cart(voucher, cart)
    if voucher.type == VoucherType.SHIPPING:
        return _get_shipping_voucher_discount_for_cart(voucher, cart)
    if voucher.type in (VoucherType.PRODUCT, VoucherType.CATEGORY):
        return _get_product_or_category_voucher_discount_for_cart(
            voucher, cart)
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


def recalculate_cart_discount(cart):
    """Recalculate `cart.discount` based on the voucher.

    Will clear both voucher and discount if the discount is no longer
    applicable.
    """
    voucher = get_voucher_for_cart(cart)
    if voucher is not None:
        try:
            cart.discount_amount = get_voucher_discount_for_cart(voucher, cart)
            cart.discount_name = voucher.name
            cart.save()
        except NotApplicable:
            remove_discount_from_cart(cart)
    else:
        remove_discount_from_cart(cart)


def remove_discount_from_cart(cart):
    """Remove voucher data from cart."""
    cart.discount_amount = ZERO_MONEY
    cart.discount_name = None
    cart.voucher_code = None
    cart.save()


def get_taxes_for_cart(cart, default_taxes):
    """Return taxes based on shipping address (if set) or default one."""
    if cart.shipping_address:
        return get_taxes_for_country(cart.shipping_address.country)

    return default_taxes


@transaction.atomic
def create_order(cart, tracking_code, discounts, taxes):
    """Create an order from the cart.

    Each order will get a private copy of both the billing and the shipping
    address (if shipping).

    If any of the addresses is new and the user is logged in the address
    will also get saved to that user's address book.

    Current user's language is saved in the order so we can later determine
    which language to use when sending email.
    """
    # FIXME: save locale along with the language
    voucher = get_voucher_for_cart(
        cart, vouchers=Voucher.objects.active(
            date=date.today()).select_for_update())

    if cart.voucher_code and not voucher:
        # Voucher expired in meantime, abort order placement
        return None

    billing_address = cart.billing_address

    if cart.is_shipping_required():
        shipping_address = cart.shipping_address
        shipping_method = cart.shipping_method
        shipping_method_name = smart_text(shipping_method)
    else:
        shipping_address = None
        shipping_method = None
        shipping_method_name = None

    if cart.user:
        if (
            shipping_address and
            shipping_address not in cart.user.addresses.all()
        ):
            store_user_address(cart.user, shipping_address, shipping=True)
        if billing_address not in cart.user.addresses.all():
            store_user_address(cart.user, billing_address, billing=True)
        if shipping_address:
            shipping_address = shipping_address.get_copy()
        billing_address = billing_address.get_copy()

    order_data = {
        'language_code': get_language(),
        'billing_address': billing_address,
        'shipping_address': shipping_address,
        'tracking_client_id': tracking_code,
        'shipping_method': shipping_method,
        'shipping_method_name': shipping_method_name,
        'shipping_price': cart.get_shipping_price(taxes),
        'total': cart.get_total(taxes=taxes)}

    if cart.user:
        order_data['user'] = cart.user
        order_data['user_email'] = cart.user.email
    else:
        order_data['user_email'] = cart.user_email

    if voucher is not None:
        order_data['voucher'] = voucher
        order_data['discount_amount'] = cart.discount_amount
        order_data['discount_name'] = cart.discount_name

    order = Order.objects.create(**order_data)

    for line in cart.lines.all():
        add_variant_to_order(
            order, line.variant, line.quantity, discounts, taxes,
            add_to_existing=False)

    if voucher is not None:
        increase_voucher_usage(voucher)

    if cart.note:
        order.notes.create(user=order.user, content=cart.note)

    return order
