from django.template import Library
from payments import PaymentStatus

from ...order import OrderStatus

register = Library()


ERRORS = {PaymentStatus.ERROR, PaymentStatus.REJECTED}
SUCCESSES = {
    OrderStatus.FULLY_PAID, OrderStatus.SHIPPED,
    PaymentStatus.CONFIRMED, PaymentStatus.REFUNDED}


@register.inclusion_tag('status_label.html')
def render_status(status, status_display=None):
    if status in ERRORS:
        label_cls = 'danger'
    elif status in SUCCESSES:
        label_cls = 'success'
    else:
        label_cls = 'default'
    return {'label_cls': label_cls, 'status': status_display or status}
