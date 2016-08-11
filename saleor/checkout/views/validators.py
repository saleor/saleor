from functools import wraps

from django.core.exceptions import ValidationError
from django.shortcuts import redirect


def validate_cart(view):
    @wraps(view)
    def func(request, checkout, cart):
        if cart:
            return view(request, checkout)
        else:
            return redirect('cart:index')
    return func


def validate_shipping_address(view):
    @wraps(view)
    def func(request, checkout):
        if checkout.email is None or checkout.shipping_address is None:
            return redirect('checkout:shipping-address')
        try:
            checkout.shipping_address.full_clean()
        except ValidationError:
            return redirect('checkout:shipping-address')
        return view(request, checkout)
    return func


def validate_shipping_method(view):
    @wraps(view)
    def func(request, checkout):
        if checkout.shipping_method is None:
            return redirect('checkout:shipping-method')
        return view(request, checkout)
    return func


def validate_is_shipping_required(view):
    @wraps(view)
    def func(request, checkout):
        if not checkout.is_shipping_required:
            return redirect('checkout:summary')
        return view(request, checkout)
    return func
