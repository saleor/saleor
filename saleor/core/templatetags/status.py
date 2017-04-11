from django.template import Library
from django.utils.translation import pgettext_lazy
from payments import PaymentStatus

from ...order import OrderStatus

register = Library()


ERRORS = {PaymentStatus.ERROR, PaymentStatus.REJECTED}
SUCCESSES = {
    OrderStatus.FULLY_PAID, OrderStatus.SHIPPED,
    PaymentStatus.CONFIRMED, PaymentStatus.REFUNDED}


LABEL_DANGER = 'danger'
LABEL_SUCCESS = 'success'
LABEL_DEFAULT = 'default'


@register.inclusion_tag('status_label.html')
def render_status(status, status_display=None):
    if status in ERRORS:
        label_cls = LABEL_DANGER
    elif status in SUCCESSES:
        label_cls = LABEL_SUCCESS
    else:
        label_cls = LABEL_DEFAULT
    return {'label_cls': label_cls, 'status': status_display or status}


@register.inclusion_tag('status_label.html')
def render_availability_status(product):
    is_available = product.is_available()
    in_stock = product.is_in_stock()
    requires_variants = product.product_class.has_variants

    if not product.is_published:
        label_cls = LABEL_DANGER
        status = pgettext_lazy('Product status', 'not published')
    elif requires_variants and not product.variants.exists():
        label_cls = LABEL_DANGER
        status = pgettext_lazy('Product status', 'variants missing')
    elif not in_stock:
        label_cls = LABEL_DANGER
        status = pgettext_lazy('Product status', 'out of stock')
    elif not is_available and product.available_on is not None:
        label_cls = LABEL_DANGER
        status = pgettext_lazy('Product status', 'not yet available')
    else:
        label_cls = LABEL_SUCCESS
        status = pgettext_lazy('Product status', 'ready for purchase')
    return {'status': status, 'label_cls': label_cls}
