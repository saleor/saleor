from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from order.models import Order


def success(request, token):
    order = get_object_or_404(Order, token=token)
    return TemplateResponse(request, 'order/success.html', {'order': order})
