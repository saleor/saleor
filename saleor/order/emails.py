from celery import shared_task
from django.conf import settings
from django.contrib.sites.models import Site
from templated_email import send_templated_mail

CONFIRM_ORDER_TEMPLATE = 'order/confirm_order'
CONFIRM_PAYMENT_TEMPLATE = 'order/payment/confirm_payment'
CONFIRM_NOTE_TEMPLATE = 'order/note/confirm_note'


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


@shared_task
def send_order_confirmation(email, url, order_pk):
    from .models import Order
    order = Order.objects.get(pk=order_pk)
    _send_confirmation(email, url, CONFIRM_ORDER_TEMPLATE, {'order': order})


@shared_task
def send_payment_confirmation(email, url):
    _send_confirmation(email, url, CONFIRM_PAYMENT_TEMPLATE)


@shared_task
def send_note_confirmation(email, url):
    _send_confirmation(email, url, CONFIRM_NOTE_TEMPLATE)
