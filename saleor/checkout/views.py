from django.http.response import Http404
from django.shortcuts import redirect

from ..cart import Cart
from ..cart.utils import adjust_quantities
from . import Checkout


def details(request, step):
    if not request.cart:
        return redirect('cart:index')
    # Check cart
    cart = Cart.for_session_cart(request.cart)
    cart_modified = adjust_quantities(request, cart)
    if cart_modified:
        return redirect('cart:index')
    checkout = Checkout(request)
    if not step:
        return redirect(checkout.get_next_step())
    try:
        step = checkout[step]
    except KeyError:
        raise Http404()
    response = step.process(extra_context={'checkout': checkout})
    if not response:
        checkout.save()
        return redirect(checkout.get_next_step())
    return response
