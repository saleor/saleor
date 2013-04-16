from authorizenet.utils import process_payment
from django.utils.translation import ugettext
import urllib2
from payments.signals import status_changed
from django.dispatch import receiver


class PaymentFailure(Exception):
    def __init__(self, error_message):
        super(PaymentFailure, self).__init__(error_message)
        self.error_message = error_message


def authorizenet(order, cleaned_data, capture=True):
    trans_type = 'AUTH_CAPTURE' if capture else 'AUTH_ONLY'
    address = order.billing_address
    data = {
        'card_num': cleaned_data['number'],
        'exp_date': cleaned_data['expiration'],
        'amount': order.get_total().gross,
        'type': trans_type,
        'first_name': address.first_name,
        'last_name': address.last_name,
        'company': address.company_name,
        'address': '%s %s' % (address.street_address_1,
                              address.street_address_2),
        'city': address.city,
        'state': address.country_area,
        'zip': address.postal_code,
        'country': address.country,
        'phone': address.phone
    }
    if cleaned_data['cvv2']:
        data['card_code'] = cleaned_data['cvv2']
    if order.user:
        data['cust_id'] = str(order.user.id)
        data['email'] = order.user.email
    try:
        response = process_payment(data, {})
    except urllib2.URLError:
        raise PaymentFailure(ugettext('Could not connect to the gateway.'))
    if not response.is_approved:
        raise PaymentFailure(response.response_reason_text)


@receiver(status_changed)
def order_status_change(sender, instance, **kwargs):
    order = instance.order
    if order.is_full_paid():
        order.status = 'complete'
        order.save()
