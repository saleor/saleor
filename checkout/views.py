from checkout import Checkout
from django.http.response import Http404
from django.shortcuts import redirect


def details(request, step):
    if not request.cart:
        return redirect('cart:index')
    checkout = Checkout(request)
    if not step:
        return redirect(checkout.get_next_step())
    try:
        step = checkout[step]
    except KeyError:
        raise Http404()
    response = step.process()
    if hasattr(response, 'context_data'):
        response.context_data['checkout'] = checkout
    return response or redirect(checkout.get_next_step())

