import logging

logger = logging.getLogger(__name__)


class AddressType:
    BILLING = "billing"
    SHIPPING = "shipping"

    CHOICES = [
        (BILLING, "Billing"),
        (SHIPPING, "Shipping"),
    ]
