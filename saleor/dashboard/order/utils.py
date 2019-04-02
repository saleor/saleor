from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import get_template

from ...checkout import AddressType
from ...checkout.utils import _get_products_voucher_discount
from ...core.utils.taxes import ZERO_MONEY
from ...discount import VoucherType
from ...discount.utils import (
    get_shipping_voucher_discount, get_value_voucher_discount)

INVOICE_TEMPLATE = 'dashboard/order/pdf/invoice.html'
PACKING_SLIP_TEMPLATE = 'dashboard/order/pdf/packing_slip.html'


def get_statics_absolute_url(request):
    site = get_current_site(request)
    absolute_url = '%(protocol)s://%(domain)s%(static_url)s' % {
        'protocol': 'https' if request.is_secure() else 'http',
        'domain': site.domain,
        'static_url': settings.STATIC_URL}
    return absolute_url


def _create_pdf(rendered_template, absolute_url):
    from weasyprint import HTML
    pdf_file = (HTML(string=rendered_template, base_url=absolute_url)
                .write_pdf())
    return pdf_file


def create_invoice_pdf(order, absolute_url):
    ctx = {
        'order': order,
        'site': Site.objects.get_current()}
    rendered_template = get_template(INVOICE_TEMPLATE).render(ctx)
    pdf_file = _create_pdf(rendered_template, absolute_url)
    return pdf_file, order


def create_packing_slip_pdf(order, fulfillment, absolute_url):
    ctx = {
        'order': order,
        'fulfillment': fulfillment,
        'site': Site.objects.get_current()}
    rendered_template = get_template(PACKING_SLIP_TEMPLATE).render(ctx)
    pdf_file = _create_pdf(rendered_template, absolute_url)
    return pdf_file, order


def update_order_with_user_addresses(order):
    """Update addresses in an order based on a user assigned to an order."""
    if order.shipping_address:
        order.shipping_address.delete()
        order.shipping_address = None

    if order.billing_address:
        order.billing_address.delete()
        order.billing_address = None

    if order.user:
        order.billing_address = (
            order.user.default_billing_address.get_copy()
            if order.user.default_billing_address else None)
        order.shipping_address = (
            order.user.default_shipping_address.get_copy()
            if order.user.default_shipping_address else None)

    order.save(update_fields=['billing_address', 'shipping_address'])


def get_voucher_discount_for_order(order):
    """Calculate discount value depending on voucher and discount types.

    Raise NotApplicable if voucher of given type cannot be applied.
    """
    if not order.voucher:
        return ZERO_MONEY
    if order.voucher.type == VoucherType.VALUE:
        return get_value_voucher_discount(
            order.voucher, order.get_subtotal())
    if order.voucher.type == VoucherType.SHIPPING:
        return get_shipping_voucher_discount(
            order.voucher, order.get_subtotal(), order.shipping_price)
    if order.voucher.type in (
            VoucherType.PRODUCT, VoucherType.COLLECTION, VoucherType.CATEGORY):
        return _get_products_voucher_discount(order, order.voucher)
    raise NotImplementedError('Unknown discount type')


def save_address_in_order(order, address, address_type):
    """Save new address of a given address type in an order.

    If the other type of address is empty, copy it.
    """
    if address_type == AddressType.SHIPPING:
        order.shipping_address = address
        if not order.billing_address:
            order.billing_address = address.get_copy()
    else:
        order.billing_address = address
        if not order.shipping_address:
            order.shipping_address = address.get_copy()
    order.save(update_fields=['billing_address', 'shipping_address'])


def addresses_are_equal(address_1, address_2):
    return address_1 and address_2 and address_1 == address_2


def remove_customer_from_order(order):
    """Remove related customer and user email from order.

    If billing and shipping addresses are set to related customer's default
    addresses and were not edited, remove them as well.
    """
    customer = order.user
    order.user = None
    order.user_email = ''
    order.save()

    if customer:
        equal_billing_addresses = addresses_are_equal(
            order.billing_address, customer.default_billing_address)
        if equal_billing_addresses:
            order.billing_address.delete()
            order.billing_address = None

        equal_shipping_addresses = addresses_are_equal(
            order.shipping_address, customer.default_shipping_address)
        if equal_shipping_addresses:
            order.shipping_address.delete()
            order.shipping_address = None

        if equal_billing_addresses or equal_shipping_addresses:
            order.save()
