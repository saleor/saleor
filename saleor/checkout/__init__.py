import logging

logger = logging.getLogger(__name__)

default_app_config = "saleor.checkout.app.CheckoutAppConfig"


class AddressType:
    BILLING = "billing"
    SHIPPING = "shipping"

    CHOICES = [
        (BILLING, "Billing"),
        (SHIPPING, "Shipping"),
    ]
