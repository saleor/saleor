from django.http.response import Http404
from django.shortcuts import redirect, get_object_or_404
from order.models import Order
from order.steps import OrderProcessManager


def details(request, token, step):
    order = get_object_or_404(Order, token=token)
    order_processor = OrderProcessManager(order, request)
    try:
        step = order_processor[step]
    except KeyError:
        raise Http404()
    response = step.process()
    if hasattr(response, 'context_data'):
        response.context_data['order'] = order
    return response or redirect(order_processor.get_next_step())
