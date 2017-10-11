from templated_email import send_templated_mail
from ..site.utils import get_site_name
from django.conf import settings


CONFIRMATION_TEMPLATE = 'order/confirm_order'


def send_confirmation(address, url):
    send_templated_mail(from_email=settings.ORDER_FROM_EMAIL,
                        recipient_list=[address],
                        context={'site_name': get_site_name(),
                                 'payment_url': url},
                        template_name=CONFIRMATION_TEMPLATE)
