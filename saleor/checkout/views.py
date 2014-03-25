from django.http.response import Http404
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import ugettext as _

from ..cart.utils import cart_is_ready_to_checkout
from . import Checkout


def details(request, step):
    if not request.cart:
        return redirect('cart:index')
    # Check cart
    checkout_possible = cart_is_ready_to_checkout(request.cart)
    if not checkout_possible:
        messages.warning(request, _('Sorry, checkout is impossible. '
                                  'You have to change your order'))
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
