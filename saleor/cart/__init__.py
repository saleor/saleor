import logging

from django.utils.translation import pgettext_lazy

logger = logging.getLogger(__name__)


class CartStatus:
    """Enum of possible cart statuses."""

    OPEN = 'open'
    CANCELED = 'canceled'

    CHOICES = [
        (OPEN, pgettext_lazy(
            'cart status', 'Open - currently active')),
        (CANCELED, pgettext_lazy(
            'cart status', 'Canceled - canceled by user'))]
