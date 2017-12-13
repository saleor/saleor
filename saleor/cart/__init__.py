import logging

from django.utils.translation import pgettext_lazy

logger = logging.getLogger(__name__)


class CartStatus:
    """Enum of possible cart statuses."""

    OPEN = 'open'
    SAVED = 'saved'
    WAITING_FOR_PAYMENT = 'payment'
    ORDERED = 'ordered'
    CHECKOUT = 'checkout'
    CANCELED = 'canceled'

    CHOICES = [
        (OPEN, pgettext_lazy(
            'cart status', 'Open - currently active')),
        (WAITING_FOR_PAYMENT, pgettext_lazy(
            'cart status', 'Waiting for payment')),
        (SAVED, pgettext_lazy(
            'cart status', 'Saved - for items to be purchased later')),
        (ORDERED, pgettext_lazy(
            'cart status', 'Submitted - an order was placed')),
        (CHECKOUT, pgettext_lazy(
            'cart status', 'Checkout - processed in checkout')),
        (CANCELED, pgettext_lazy(
            'cart status', 'Canceled - canceled by user'))]
