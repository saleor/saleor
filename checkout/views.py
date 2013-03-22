from .steps import CheckoutProcessManager
from cart import get_cart_from_request, CartPartitioner
from checkout import get_checkout_from_request
from django.http.response import Http404
from django.shortcuts import redirect


def index(request):
    cart = get_cart_from_request(request)
    if not cart:
        return redirect('cart:index')
    checkout = get_checkout_from_request(request)
    checkout_processor = CheckoutProcessManager(CartPartitioner(cart),
                                                checkout, request)
    return redirect(checkout_processor.get_next_step())


def details(request, step):
    cart = get_cart_from_request(request)
    if not cart:
        return redirect('cart:index')
    checkout = get_checkout_from_request(request)
    checkout_processor = CheckoutProcessManager(CartPartitioner(cart),
                                                checkout, request)
    try:
        step = checkout_processor[step]
    except KeyError:
        raise Http404()
    response = step.process()
    if hasattr(response, 'context_data'):
        response.context_data['checkout'] = checkout_processor
    return response or redirect(checkout_processor.get_next_step())

