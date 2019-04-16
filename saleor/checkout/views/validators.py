from functools import wraps

from django.core.exceptions import ValidationError
from django.shortcuts import redirect

from ..utils import is_valid_shipping_method


def validate_checkout(view):
    """Decorate a view making it require a non-empty checkout.

    If the checkout is empty, redirect to the checkout details.
    """
    @wraps(view)
    def func(request, checkout):
        if checkout:
            return view(request, checkout)
        return redirect('checkout:index')
    return func


def validate_shipping_address(view):
    """Decorate a view making it require a valid shipping address.

    If either the shipping address or customer email is empty, redirect to the
    shipping address step.

    Expects to be decorated with `@validate_checkout`.
    """
    @wraps(view)
    def func(request, checkout):
        if not checkout.email or not checkout.shipping_address:
            return redirect('checkout:shipping-address')
        try:
            checkout.shipping_address.full_clean()
        except ValidationError:
            return redirect('checkout:shipping-address')
        return view(request, checkout)
    return func


def validate_shipping_method(view):
    """Decorate a view making it require a shipping method.

    If the method is missing or incorrect, redirect to the shipping method
    step.

    Expects to be decorated with `@validate_checkout`.
    """
    @wraps(view)
    def func(request, checkout):
        if not is_valid_shipping_method(
                checkout, request.taxes, request.discounts):
            return redirect('checkout:shipping-method')
        return view(request, checkout)
    return func


def validate_is_shipping_required(view):
    """Decorate a view making it check if checkout needs shipping.

    If shipping is not needed, redirect to the checkout summary.

    Expects to be decorated with `@validate_checkout`.
    """
    @wraps(view)
    def func(request, checkout):
        if not checkout.is_shipping_required():
            return redirect('checkout:summary')
        return view(request, checkout)
    return func
