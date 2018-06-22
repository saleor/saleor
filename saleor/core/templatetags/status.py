import datetime

from django.template import Library
from payments import PaymentStatus

from ...order import OrderStatus
from ...product import ProductAvailabilityStatus, VariantAvailabilityStatus
from ...product.utils.availability import (
    get_product_availability_status, get_variant_availability_status)

register = Library()


ERRORS = {PaymentStatus.ERROR, PaymentStatus.REJECTED}
SUCCESSES = {PaymentStatus.CONFIRMED, PaymentStatus.REFUNDED}


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
def render_order_status(status, status_display=None):
    if status == OrderStatus.FULFILLED:
        label_cls = LABEL_SUCCESS
    else:
        label_cls = LABEL_DEFAULT
    return {'label_cls': label_cls, 'status': status_display or status}


@register.inclusion_tag('status_label.html')
def render_availability_status(product):
    status = get_product_availability_status(product)
    display = ProductAvailabilityStatus.get_display(status)
    if status == ProductAvailabilityStatus.READY_FOR_PURCHASE:
        label_cls = LABEL_SUCCESS
    else:
        label_cls = LABEL_DANGER
    return {'status': display, 'label_cls': label_cls}


@register.inclusion_tag('status_label.html')
def render_variant_availability_status(variant):
    status = get_variant_availability_status(variant)
    display = VariantAvailabilityStatus.get_display(status)
    if status == VariantAvailabilityStatus.AVAILABLE:
        label_cls = LABEL_SUCCESS
    else:
        label_cls = LABEL_DANGER
    return {'status': display, 'label_cls': label_cls}


@register.inclusion_tag('dashboard/includes/_page_availability.html')
def render_page_availability(page):
    today = datetime.date.today()
    is_published = (
        page.is_visible and (
            page.available_on is None or page.available_on <= today))
    ctx = {'is_published': is_published, 'page': page}
    if is_published:
        label_cls = LABEL_SUCCESS
        ctx.update({'label_cls': label_cls})
    return ctx


@register.inclusion_tag('dashboard/includes/_collection_availability.html')
def render_collection_availability(collection):
    if collection.is_published:
        label_cls = LABEL_SUCCESS
    else:
        label_cls = LABEL_DANGER
    return {'is_published': collection.is_published,
            'collection': collection,
            'label_cls': label_cls}
