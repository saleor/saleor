from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from order.models import Order


def success(request, token):
    order = get_object_or_404(Order, token=token)
    if order.status == 'complete':
        return TemplateResponse(request, 'order/success.html',
                                {'order': order})
    return redirect('order:payment:index', token=order.token)


def details(request, token):
    order = get_object_or_404(Order, token=token)
    groups = order.groups.all()
    payments = order.payments.all()
    return TemplateResponse(request, 'order/details.html',
                            {'order': order, 'groups': groups,
                             'payments': payments})
