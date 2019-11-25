from django.template import Library

from ...order import OrderStatus
from ...payment import ChargeStatus

register = Library()


SUCCESSES = {ChargeStatus.FULLY_CHARGED, ChargeStatus.FULLY_REFUNDED}


LABEL_SUCCESS = "success"
LABEL_DEFAULT = "default"


@register.inclusion_tag("status_label.html")
def render_status(status, status_display=None):
    if status in SUCCESSES:
        label_cls = LABEL_SUCCESS
    else:
        label_cls = LABEL_DEFAULT
    return {"label_cls": label_cls, "status": status_display or status}


@register.inclusion_tag("status_label.html")
def render_order_status(status, status_display=None):
    if status == OrderStatus.FULFILLED:
        label_cls = LABEL_SUCCESS
    else:
        label_cls = LABEL_DEFAULT
    return {"label_cls": label_cls, "status": status_display or status}


@register.inclusion_tag("dashboard/includes/_page_availability.html")
def render_page_availability(page):
    ctx = {"is_visible": page.is_visible, "page": page}
    if page.is_visible:
        label_cls = LABEL_SUCCESS
        ctx.update({"label_cls": label_cls})
    return ctx
