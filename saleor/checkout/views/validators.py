from functools import wraps

from django.core.exceptions import ValidationError
from django.shortcuts import redirect


def validate_cart(view):
    """Decorate a view making it require a non-empty cart.

    Expects to be decorated with `@load_checkout`.

    Changes view signature from `func(request, checkout, cart)` to
    `func(request, checkout)`.

    If the cart is empty redirects to the cart details.
    """
    @wraps(view)
    def func(request, checkout, cart):
        if cart:
            return view(request, checkout)
        return redirect('cart:index')
    return func


def validate_shipping_address(view):
    """Decorate a view making it require a valid shipping address.

    Expects to be decorated with `@validate_cart`.

    If either the shipping address or customer email is empty redirects to the
    shipping address step.
    """
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
    """Decorate a view making it require a shipping method.

    Expects to be decorated with `@validate_cart`.

    If the method is missing redirects to the shipping method step.
    """
    @wraps(view)
    def func(request, checkout):
        if checkout.shipping_method is None:
            return redirect('checkout:shipping-method')
        return view(request, checkout)
    return func


def validate_is_shipping_required(view):
    """Decorate a view making it check if checkout needs shipping.

    Expects to be decorated with `@validate_cart`.

    If shipping is not needed redirects to the checkout summary.
    """
    @wraps(view)
    def func(request, checkout):
        if not checkout.is_shipping_required:
            return redirect('checkout:summary')
        return view(request, checkout)
    return func
