from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import get_template

from ...account.models import Address
from ...product.utils import decrease_stock

INVOICE_TEMPLATE = 'dashboard/order/pdf/invoice.html'
PACKING_SLIP_TEMPLATE = 'dashboard/order/pdf/packing_slip.html'


def get_statics_absolute_url(request):
    site = get_current_site(request)
    absolute_url = '%(protocol)s://%(domain)s%(static_url)s' % {
        'protocol': 'https' if request.is_secure() else 'http',
        'domain': site.domain,
        'static_url': settings.STATIC_URL,
    }
    return absolute_url


def _create_pdf(rendered_template, absolute_url):
    from weasyprint import HTML
    pdf_file = (HTML(string=rendered_template, base_url=absolute_url)
                .write_pdf())
    return pdf_file


def create_invoice_pdf(order, absolute_url):
    ctx = {'order': order}
    rendered_template = get_template(INVOICE_TEMPLATE).render(ctx)
    pdf_file = _create_pdf(rendered_template, absolute_url)
    return pdf_file, order


def create_packing_slip_pdf(order, fulfillment, absolute_url):
    ctx = {'order': order, 'fulfillment': fulfillment}
    rendered_template = get_template(PACKING_SLIP_TEMPLATE).render(ctx)
    pdf_file = _create_pdf(rendered_template, absolute_url)
    return pdf_file, order


def fulfill_order_line(order_line, quantity):
    """Fulfill order line with given quantity."""
    decrease_stock(order_line.stock, quantity)
    order_line.quantity_fulfilled += quantity
    order_line.save(update_fields=['quantity_fulfilled'])


def update_order_with_user_addresses(order):
    """Update addresses in an order based on a user assigned to an order."""
    if order.shipping_address:
        order.shipping_address.delete()

    if order.billing_address:
        order.billing_address.delete()

    if order.user:
        order.billing_address = (
            order.user.default_billing_address.get_copy()
            if order.user.default_billing_address else None)
        order.shipping_address = (
            order.user.default_shipping_address.get_copy()
            if order.user.default_shipping_address else None)
        order.save()
