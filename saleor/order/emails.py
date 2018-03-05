from celery import shared_task
from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse
from templated_email import send_templated_mail

from ..core.utils import build_absolute_uri
from .models import Fulfillment, Order
from .email_helpers import get_order_confirmation_markup

CONFIRM_ORDER_TEMPLATE = 'source/order/confirm_order'
CONFIRM_FULFILLMENT_TEMPLATE = 'source/order/confirm_fulfillment'
UPDATE_FULFILLMENT_TEMPLATE = 'source/order/update_fulfillment'
CONFIRM_PAYMENT_TEMPLATE = 'source/order/payment/confirm_payment'
CONFIRM_NOTE_TEMPLATE = 'source/order/note/confirm_note'


def _send_confirmation(email, url, template, context=None):
    site = Site.objects.get_current()
    ctx = {
        'protocol': 'https' if settings.ENABLE_SSL else 'http',
        'site_name': site.name,
        'domain': site.domain,
        'url': url}
    if context:
        ctx.update(context)
    send_templated_mail(
        from_email=settings.ORDER_FROM_EMAIL,
        recipient_list=[email],
        context=ctx,
        template_name=template)


def collect_data_for_email(order_pk, template):
    order = Order.objects.get(pk=order_pk)
    email = order.get_user_current_email()
    url = build_absolute_uri(
        reverse('order:details', kwargs={'token': order.token}))
    return {'email': email, 'url': url, 'template': template}


@shared_task
def send_order_confirmation(order_pk):
    order = Order.objects.get(pk=order_pk)
    email_markup = get_order_confirmation_markup(order)
    context = {'order': order, 'schema_markup': email_markup}
    email_data = collect_data_for_email(order_pk, CONFIRM_ORDER_TEMPLATE)
    email_data.update({'context': context})
    _send_confirmation(**email_data)


@shared_task
def send_fulfillment_confirmation(order_pk, fulfillment_pk):
    email_data = collect_data_for_email(order_pk, CONFIRM_FULFILLMENT_TEMPLATE)
    fulfillment = Fulfillment.objects.get(pk=fulfillment_pk)
    email_data.update({'context': {'fulfillment': fulfillment}})
    _send_confirmation(**email_data)


@shared_task
def send_fulfillment_update(order_pk, fulfillment_pk):
    email_data = collect_data_for_email(order_pk, UPDATE_FULFILLMENT_TEMPLATE)
    fulfillment = Fulfillment.objects.get(pk=fulfillment_pk)
    email_data.update({'context': {'fulfillment': fulfillment}})
    _send_confirmation(**email_data)


@shared_task
def send_payment_confirmation(order_pk):
    email_data = collect_data_for_email(order_pk, CONFIRM_PAYMENT_TEMPLATE)
    _send_confirmation(**email_data)


@shared_task
def send_note_confirmation(order_pk):
    email_data = collect_data_for_email(order_pk, CONFIRM_NOTE_TEMPLATE)
    _send_confirmation(**email_data)
