from django.shortcuts import get_object_or_404, redirect
from functools import wraps

from .models import Order


def check_order_status(func):

    @wraps(func)
    def decorator(*args, **kwargs):
        token = kwargs.pop('token')
        order = get_object_or_404(Order, token=token)
        if order.status == 'fully-paid':
            return redirect('order:success', token=order.token)
        kwargs['order'] = order
        return func(*args, **kwargs)

    return decorator
