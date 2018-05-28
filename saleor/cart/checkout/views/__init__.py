from django.shortcuts import redirect
from django.template.response import TemplateResponse

from ....account.forms import LoginForm
from ....cart.models import Cart
from ....cart.utils import get_or_empty_db_cart
from ..forms import CartShippingMethodForm
from ..utils import get_cart_data_for_checkout, get_taxes_for_cart
from .discount import add_voucher_form, validate_voucher
from .shipping import (
    anonymous_user_shipping_address_view, user_shipping_address_view)
from .summary import (
    anonymous_summary_without_shipping, summary_with_shipping_view,
    summary_without_shipping)
from .validators import (
    validate_cart, validate_is_shipping_required, validate_shipping_address,
    validate_shipping_method)


@get_or_empty_db_cart(Cart.objects.for_display())
@validate_cart
def login(request, cart):
    """Allow the user to log in prior to checkout."""
    if request.user.is_authenticated:
        return redirect('cart:checkout-index')
    form = LoginForm()
    return TemplateResponse(request, 'checkout/login.html', {'form': form})


@get_or_empty_db_cart(Cart.objects.for_display())
@validate_cart
@validate_is_shipping_required
def index_view(request, cart):
    """Redirect to the initial step of checkout."""
    return redirect('cart:checkout-shipping-address')


@get_or_empty_db_cart(Cart.objects.for_display())
@validate_voucher
@validate_cart
@validate_is_shipping_required
@add_voucher_form
def shipping_address_view(request, cart):
    """Display the correct shipping address step."""
    if request.user.is_authenticated:
        return user_shipping_address_view(request, cart)
    return anonymous_user_shipping_address_view(request, cart)


@get_or_empty_db_cart(Cart.objects.for_display())
@validate_voucher
@validate_cart
@validate_is_shipping_required
@validate_shipping_address
@add_voucher_form
def shipping_method_view(request, cart):
    """Display the shipping method selection step."""
    taxes = get_taxes_for_cart(cart, request.taxes)
    form = CartShippingMethodForm(
        request.POST or None, taxes=taxes, instance=cart,
        initial={'shipping_method': cart.shipping_method})

    if form.is_valid():
        form.save()
        return redirect('cart:checkout-summary')

    ctx = get_cart_data_for_checkout(cart, request.discounts, taxes)
    ctx.update({'shipping_method_form': form})
    return TemplateResponse(request, 'checkout/shipping_method.html', ctx)


@get_or_empty_db_cart(Cart.objects.for_display())
@validate_voucher
@validate_cart
@add_voucher_form
def summary_view(request, cart):
    """Display the correct order summary."""
    if cart.is_shipping_required():
        view = validate_shipping_address(summary_with_shipping_view)
        view = validate_shipping_method(view)
        return view(request, cart)
    if request.user.is_authenticated:
        return summary_without_shipping(request, cart)
    return anonymous_summary_without_shipping(request, cart)
