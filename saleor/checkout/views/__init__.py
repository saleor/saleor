from django.shortcuts import redirect
from django.template.response import TemplateResponse

from ..forms import ShippingMethodForm
from .discount import add_voucher_form, validate_voucher
from .validators import (
    validate_cart, validate_shipping_address,
    validate_shipping_method, validate_is_shipping_required)
from .shipping import anonymous_user_shipping_address_view, user_shipping_address_view
from .summary import summary_with_shipping_view, anonymous_summary_without_shipping, \
    summary_without_shipping


@validate_cart
@validate_is_shipping_required
def index_view(request, checkout):
    return redirect('checkout:shipping-address')


@validate_voucher
@validate_cart
@validate_is_shipping_required
@add_voucher_form
def shipping_address_view(request, checkout):
    if request.user.is_authenticated():
        return user_shipping_address_view(request, checkout)
    return anonymous_user_shipping_address_view(request, checkout)


@validate_voucher
@validate_cart
@validate_is_shipping_required
@validate_shipping_address
@add_voucher_form
def shipping_method_view(request, checkout):
    country_code = checkout.shipping_address.country.code
    shipping_method_form = ShippingMethodForm(
        country_code, request.POST or None, initial={'method': checkout.shipping_method})
    if shipping_method_form.is_valid():
        checkout.shipping_method = shipping_method_form.cleaned_data['method']
        return redirect('checkout:summary')
    return TemplateResponse(request, 'checkout/shipping_method.html', context={
        'shipping_method_form': shipping_method_form, 'checkout': checkout})


@validate_voucher
@validate_cart
@add_voucher_form
def summary_view(request, checkout):
    if checkout.is_shipping_required:
        view = validate_shipping_address(summary_with_shipping_view)
        view = validate_shipping_method(view)
        return view(request, checkout)
    elif request.user.is_authenticated():
        return summary_without_shipping(request, checkout)
    else:
        return anonymous_summary_without_shipping(request, checkout)
