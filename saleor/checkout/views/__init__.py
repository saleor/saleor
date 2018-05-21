from django.shortcuts import redirect
from django.template.response import TemplateResponse

from .discount import add_voucher_form, validate_voucher
from .summary import (
    summary_with_shipping_view, anonymous_summary_without_shipping,
    summary_without_shipping)
from .validators import (
    validate_cart, validate_shipping_address,
    validate_shipping_method, validate_is_shipping_required)
from ..core import load_checkout
from ...account.forms import LoginForm


@load_checkout
@validate_cart
@validate_is_shipping_required
def index_view(request, cart, checkout):
    """Redirect to the initial step of checkout."""
    return redirect('checkout:shipping-address')


@load_checkout
@validate_voucher
@validate_cart
@add_voucher_form
def summary_view(request, cart, checkout):
    """Display the correct order summary."""
    if checkout.is_shipping_required:
        view = validate_shipping_address(summary_with_shipping_view)
        view = validate_shipping_method(view)
        return view(request, cart, checkout)
    if request.user.is_authenticated:
        return summary_without_shipping(request, cart, checkout)
    return anonymous_summary_without_shipping(request, cart, checkout)


@load_checkout
@validate_cart
def login(request, cart, checkout):
    """Allow the user to log in prior to checkout."""
    if request.user.is_authenticated:
        return redirect('checkout:index')
    form = LoginForm()
    return TemplateResponse(request, 'checkout/login.html', {'form': form})
