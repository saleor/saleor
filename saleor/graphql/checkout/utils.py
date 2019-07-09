from saleor.shipping.models import ShippingMethod
from ...checkout.utils import get_valid_shipping_methods
from ...checkout.models import Checkout


def update_shipping_method_checkout(
    checkout: Checkout, discounts, *, country_code=None
) -> ShippingMethod:
    """Check if current shipping method is valid. If so - return it.
    If current method is invalid assign cheapest shipping method available.
    """
    valid_methods = get_valid_shipping_methods(
        checkout, discounts, country_code=country_code
    )

    if checkout.shipping_method in valid_methods:
        return checkout.shipping_method

    return valid_methods.first()
