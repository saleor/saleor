from django.shortcuts import redirect
from django.template.response import TemplateResponse

from ....checkout.core import load_checkout
from ....checkout.views import (
    add_voucher_form, validate_cart, validate_is_shipping_required,
    validate_shipping_address, validate_voucher)
from ..forms import CartShippingMethodForm
from ..utils import get_checkout_data
from .shipping import (
    anonymous_user_shipping_address_view, user_shipping_address_view)


@load_checkout
@validate_voucher
@validate_cart
@validate_is_shipping_required
@add_voucher_form
def shipping_address_view(request, cart, checkout):
    """Display the correct shipping address step."""
    if request.user.is_authenticated:
        return user_shipping_address_view(request, cart, checkout)
    return anonymous_user_shipping_address_view(request, cart, checkout)


@load_checkout
@validate_voucher
@validate_cart
@validate_is_shipping_required
@validate_shipping_address
@add_voucher_form
def shipping_method_view(request, cart, checkout):
    """Display the shipping method selection step."""
    taxes = checkout.get_taxes()
    form = CartShippingMethodForm(
        request.POST or None, taxes=taxes, instance=cart,
        initial={'shipping_method': cart.shipping_method})

    if form.is_valid():
        form.save()
        return redirect('checkout:summary')

    ctx = get_checkout_data(cart, request.discounts, taxes)
    ctx.update({
        'checkout': checkout,
        'shipping_method_form': form})
    return TemplateResponse(request, 'checkout/shipping_method.html', ctx)
