from django.http.response import Http404
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import ugettext as _

from ..cart import Cart
from . import Checkout


def details(request, step):
    if not request.cart:
        return redirect('cart:index')
    # Check cart
    cart = Cart.for_session_cart(request.cart)
    cart_modified = cart.adjust_quantities()
    if cart_modified:
        messages.warning(request, _('Oops, looks like there is a '
                                    'problem with your shopping cart.'))
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
