from celery import shared_task
from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse
from templated_email import send_templated_mail

from ..core.utils import build_absolute_uri
from ..seo.schema.email import get_order_confirmation_markup
from .models import Fulfillment, Order

CONFIRM_ORDER_TEMPLATE = 'order/confirm_order'
CONFIRM_FULFILLMENT_TEMPLATE = 'order/confirm_fulfillment'
UPDATE_FULFILLMENT_TEMPLATE = 'order/update_fulfillment'
CONFIRM_PAYMENT_TEMPLATE = 'order/payment/confirm_payment'
CONFIRM_NOTE_TEMPLATE = 'order/note/confirm_note'


def get_email_context(order_token):
    """Prepares context required for email template rendering."""
    site = Site.objects.get_current()
    order_url = build_absolute_uri(
        reverse('order:details', kwargs={'token': order_token}))
    ctx = {
        'protocol': 'https' if settings.ENABLE_SSL else 'http',
        'site_name': site.name,
        'domain': site.domain,
        'url': order_url}
    return ctx


def collect_data_for_email(order_pk, template):
    """Collects data required for email sending.

    Args:
        order_pk (int): order primary key
        template (str): email template path
    """
    order = Order.objects.get(pk=order_pk)
    recipient_email = order.get_user_current_email()
    email_context = get_email_context(order.token)

    # Order confirmation template requires additional information
    if template == CONFIRM_ORDER_TEMPLATE:
        email_markup = get_order_confirmation_markup(order)
        email_context.update(
            {'order': order, 'schema_markup': email_markup})

    return {
        'recipient_list': [recipient_email], 'template_name': template,
        'context': email_context, 'from_email': settings.ORDER_FROM_EMAIL}


def collect_data_for_fullfillment_email(order_pk, template, fulfillment_pk):
    fulfillment = Fulfillment.objects.get(pk=fulfillment_pk)
    email_data = collect_data_for_email(order_pk, template)
    email_data['context'].update({'fulfillment': fulfillment})
    return email_data


@shared_task
def send_order_confirmation(order_pk):
    """Sends order confirmation email."""
    email_data = collect_data_for_email(order_pk, CONFIRM_ORDER_TEMPLATE)
    send_templated_mail(**email_data)


@shared_task
def send_fulfillment_confirmation(order_pk, fulfillment_pk):
    email_data = collect_data_for_fullfillment_email(
        order_pk, CONFIRM_FULFILLMENT_TEMPLATE, fulfillment_pk)
    send_templated_mail(**email_data)


@shared_task
def send_fulfillment_update(order_pk, fulfillment_pk):
    email_data = collect_data_for_fullfillment_email(
        order_pk, UPDATE_FULFILLMENT_TEMPLATE, fulfillment_pk)
    send_templated_mail(**email_data)


@shared_task
def send_payment_confirmation(order_pk):
    """Sends payment confirmation email."""
    email_data = collect_data_for_email(order_pk, CONFIRM_PAYMENT_TEMPLATE)
    send_templated_mail(**email_data)


@shared_task
def send_note_confirmation(order_pk):
    """Notifies customer, when new note was added to an order."""
    email_data = collect_data_for_email(order_pk, CONFIRM_NOTE_TEMPLATE)
    send_templated_mail(**email_data)
