from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import get_template
from django.utils.translation import pgettext

from ...checkout import AddressType
from ...core.taxes import zero_money
from ...discount import VoucherType
from ...discount.models import NotApplicable
from ...discount.utils import get_products_voucher_discount, validate_voucher_in_order

INVOICE_TEMPLATE = "dashboard/order/pdf/invoice.html"
PACKING_SLIP_TEMPLATE = "dashboard/order/pdf/packing_slip.html"


def get_statics_absolute_url(request):
    site = get_current_site(request)
    absolute_url = "%(protocol)s://%(domain)s%(static_url)s" % {
        "protocol": "https" if request.is_secure() else "http",
        "domain": site.domain,
        "static_url": settings.STATIC_URL,
    }
    return absolute_url


def _create_pdf(rendered_template, absolute_url):
    from weasyprint import HTML

    pdf_file = HTML(string=rendered_template, base_url=absolute_url).write_pdf()
    return pdf_file


def create_invoice_pdf(order, absolute_url):
    ctx = {"order": order, "site": Site.objects.get_current()}
    rendered_template = get_template(INVOICE_TEMPLATE).render(ctx)
    pdf_file = _create_pdf(rendered_template, absolute_url)
    return pdf_file, order


def create_packing_slip_pdf(order, fulfillment, absolute_url):
    ctx = {
        "order": order,
        "fulfillment": fulfillment,
        "site": Site.objects.get_current(),
    }
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
            if order.user.default_billing_address
            else None
        )
        order.shipping_address = (
            order.user.default_shipping_address.get_copy()
            if order.user.default_shipping_address
            else None
        )

    order.save(update_fields=["billing_address", "shipping_address"])


def get_prices_of_discounted_products(order, discounted_products):
    """Get prices of variants belonging to the discounted products."""
    line_prices = []
    if discounted_products:
        for line in order:
            if line.variant.product in discounted_products:
                line_prices.extend([line.unit_price_gross] * line.quantity)
    return line_prices


def get_prices_of_products_in_discounted_collections(order, discounted_collections):
    """Get prices of variants belonging to the discounted collections."""
    line_prices = []
    if discounted_collections:
        for line in order:
            if not line.variant:
                continue
            product_collections = line.variant.product.collections.all()
            if set(product_collections).intersection(discounted_collections):
                line_prices.extend([line.unit_price_gross] * line.quantity)
    return line_prices


def get_prices_of_products_in_discounted_categories(order, discounted_categories):
    """Get prices of variants belonging to the discounted categories.

    Product must be assigned directly to the discounted category, assigning
    product to child category won't work.
    """
    # If there's no discounted collections,
    # it means that all of them are discounted
    line_prices = []
    if discounted_categories:
        discounted_categories = set(discounted_categories)
        for line in order:
            if not line.variant:
                continue
            product_category = line.variant.product.category
            if product_category in discounted_categories:
                line_prices.extend([line.unit_price_gross] * line.quantity)
    return line_prices


def get_products_voucher_discount_for_order(order, voucher):
    """Calculate products discount value for a voucher, depending on its type."""
    prices = None
    if voucher.type == VoucherType.PRODUCT:
        prices = get_prices_of_discounted_products(order, voucher.products.all())
    elif voucher.type == VoucherType.COLLECTION:
        prices = get_prices_of_products_in_discounted_collections(
            order, voucher.collections.all()
        )
    elif voucher.type == VoucherType.CATEGORY:
        prices = get_prices_of_products_in_discounted_categories(
            order, voucher.categories.all()
        )
    if not prices:
        msg = pgettext(
            "Voucher not applicable", "This offer is only valid for selected items."
        )
        raise NotApplicable(msg)
    return get_products_voucher_discount(voucher, prices)


def get_voucher_discount_for_order(order):
    """Calculate discount value depending on voucher and discount types.

    Raise NotApplicable if voucher of given type cannot be applied.
    """
    if not order.voucher:
        return zero_money()
    validate_voucher_in_order(order)
    subtotal = order.get_subtotal()
    if order.voucher.type == VoucherType.ENTIRE_ORDER:
        return order.voucher.get_discount_amount_for(subtotal.gross)
    if order.voucher.type == VoucherType.SHIPPING:
        return order.voucher.get_discount_amount_for(order.shipping_price)
    if order.voucher.type in (
        VoucherType.PRODUCT,
        VoucherType.COLLECTION,
        VoucherType.CATEGORY,
        VoucherType.SPECIFIC_PRODUCT,
    ):
        return get_products_voucher_discount_for_order(order, order.voucher)
    raise NotImplementedError("Unknown discount type")


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
    order.save(update_fields=["billing_address", "shipping_address"])


def addresses_are_equal(address_1, address_2):
    return address_1 and address_2 and address_1 == address_2


def remove_customer_from_order(order):
    """Remove related customer and user email from order.

    If billing and shipping addresses are set to related customer's default
    addresses and were not edited, remove them as well.
    """
    customer = order.user
    order.user = None
    order.user_email = ""
    order.save()

    if customer:
        equal_billing_addresses = addresses_are_equal(
            order.billing_address, customer.default_billing_address
        )
        if equal_billing_addresses:
            order.billing_address.delete()
            order.billing_address = None

        equal_shipping_addresses = addresses_are_equal(
            order.shipping_address, customer.default_shipping_address
        )
        if equal_shipping_addresses:
            order.shipping_address.delete()
            order.shipping_address = None

        if equal_billing_addresses or equal_shipping_addresses:
            order.save()
