from django.shortcuts import redirect
from django.template.response import TemplateResponse

from .discount import add_voucher_form, validate_voucher
from .validators import validate_cart, validate_is_shipping_required
from ..core import load_checkout
from ...account.forms import LoginForm


@load_checkout
@validate_cart
@validate_is_shipping_required
def index_view(request, cart, checkout):
    """Redirect to the initial step of checkout."""
    return redirect('checkout:shipping-address')


@load_checkout
@validate_cart
def login(request, cart, checkout):
    """Allow the user to log in prior to checkout."""
    if request.user.is_authenticated:
        return redirect('checkout:index')
    form = LoginForm()
    return TemplateResponse(request, 'checkout/login.html', {'form': form})
