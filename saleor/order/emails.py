from templated_email import send_templated_mail
from django.conf import settings
from django.contrib.sites.models import Site
from celery import shared_task

CONFIRM_ORDER_TEMPLATE = 'order/confirm_order'
CONFIRM_PAYMENT_TEMPLATE = 'order/payment/confirm_payment'


def _send_confirmation(address, url, template):
    site = Site.objects.get_current()
    send_templated_mail(
        from_email=settings.ORDER_FROM_EMAIL,
        recipient_list=[address],
        context={'site_name': site.name,
                 'url': url},
        template_name=template)


@shared_task
def send_order_confirmation(address, url):
    _send_confirmation(address, url, CONFIRM_ORDER_TEMPLATE)


@shared_task
def send_payment_confirmation(address, url):
    _send_confirmation(address, url, CONFIRM_PAYMENT_TEMPLATE)
