from .steps import CheckoutProcessManager
from cart import get_cart_from_request
from django.http.response import Http404
from django.shortcuts import redirect


def index(request):
    cart = get_cart_from_request(request)
    if not cart:
        return redirect('cart:index')
    checkout = CheckoutProcessManager(cart, request)
    return redirect(checkout.get_next_step())


def details(request, step):
    cart = get_cart_from_request(request)
    if not cart:
        return redirect('cart:index')
    checkout = CheckoutProcessManager(cart, request)
    try:
        step = checkout[step]
    except KeyError:
        raise Http404()
    response = step.process()
    if hasattr(response, 'context_data'):
        response.context_data['checkout'] = checkout
    return response or redirect(checkout.get_next_step())

