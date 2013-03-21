from django.http.response import Http404
from django.shortcuts import redirect, get_object_or_404
from order.models import Order
#from order.steps import CheckoutProcessManager


#def details(request, token, step):
#    order = get_object_or_404(Order, token=token)
#    checkout = CheckoutProcessManager(order, request)
#    try:
#        step = checkout[step]
#    except KeyError:
#        raise Http404()
#    response = step.process()
#    if hasattr(response, 'context_data'):
#        response.context_data['checkout'] = checkout
#    return response or redirect(checkout.get_next_step())

