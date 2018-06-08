import logging

from django.utils.translation import pgettext_lazy

logger = logging.getLogger(__name__)


class AddressType:
    BILLING = 'billing'
    SHIPPING = 'shipping'

    CHOICES = [
        (BILLING, pgettext_lazy(
            'Type of address used to fulfill order',
            'Billing'
        )),
        (SHIPPING, pgettext_lazy(
            'Type of address used to fulfill order',
            'Shipping'
        ))]
