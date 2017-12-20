"""Cart-related context processors."""
from .utils import get_cart_from_request


def cart_counter(request):
    """Expose the number of items in cart."""
    cart = get_cart_from_request(request)
    return {'cart_counter': cart.quantity}
