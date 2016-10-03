from __future__ import unicode_literals
from .decorators import get_cart_from_request


def cart_counter(request):
    """ Return number of items from cart """
    cart = get_cart_from_request(request)
    return {'cart_counter': cart.quantity}

