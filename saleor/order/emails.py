from celery import shared_task
from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse
from templated_email import send_templated_mail

from ..core.utils import build_absolute_uri

CONFIRM_ORDER_TEMPLATE = 'source/order/confirm_order'
CONFIRM_PAYMENT_TEMPLATE = 'source/order/payment/confirm_payment'
CONFIRM_NOTE_TEMPLATE = 'source/order/note/confirm_note'


@shared_task
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


def collect_data_for_email(order, template):
    email = order.get_user_current_email()
    url = build_absolute_uri(
        reverse('order:details', kwargs={'token': order.token}))
    return {'email': email, 'url': url, 'template': template}


def send_order_confirmation(order):
    email_data = collect_data_for_email(order, CONFIRM_ORDER_TEMPLATE)
    email_data.update({'context': {'order': order}})
    _send_confirmation.delay(**email_data)


def send_payment_confirmation(order):
    email_data = collect_data_for_email(order, CONFIRM_PAYMENT_TEMPLATE)
    _send_confirmation.delay(**email_data)


def send_note_confirmation(order):
    email_data = collect_data_for_email(order, CONFIRM_NOTE_TEMPLATE)
    _send_confirmation.delay(**email_data)
