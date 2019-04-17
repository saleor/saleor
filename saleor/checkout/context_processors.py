"""Checkout-related context processors."""
from .utils import get_checkout_from_request


def checkout_counter(request):
    """Expose the number of items in checkout."""
    checkout = get_checkout_from_request(request)
    return {'checkout_counter': checkout.quantity}
