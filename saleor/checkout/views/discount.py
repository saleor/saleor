from datetime import date
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext
from django.views.decorators.http import require_POST

from ...discount.models import Voucher
from ..forms import CartVoucherForm
from ..models import Cart
from ..utils import (
    get_or_empty_db_cart, get_taxes_for_cart, recalculate_cart_discount,
    remove_voucher_from_cart)


def add_voucher_form(view):
    """Decorate a view injecting a voucher form and handling its submission."""
    @wraps(view)
    def func(request, cart):
        prefix = 'discount'
        data = {k: v for k, v in request.POST.items() if k.startswith(prefix)}
        voucher_form = CartVoucherForm(
            data or None, prefix=prefix, instance=cart)
        if voucher_form.is_bound:
            if voucher_form.is_valid():
                voucher_form.save()
                next_url = request.GET.get(
                    'next', request.META['HTTP_REFERER'])
                return redirect(next_url)
            else:
                remove_voucher_from_cart(cart)
                # if only discount form was used we clear post for other forms
                request.POST = {}
        else:
            taxes = get_taxes_for_cart(cart, request.taxes)
            recalculate_cart_discount(cart, request.discounts, taxes)
        response = view(request, cart)
        if isinstance(response, TemplateResponse):
            response.context_data['voucher_form'] = voucher_form
        return response
    return func


def validate_voucher(view):
    """Decorate a view making it check whether a discount voucher is valid.

    If the voucher is invalid it will be removed and the user will be
    redirected to the checkout summary view.
    """
    @wraps(view)
    def func(request, cart):
        if cart.voucher_code:
            try:
                Voucher.objects.active(date=date.today()).get(
                    code=cart.voucher_code)
            except Voucher.DoesNotExist:
                remove_voucher_from_cart(cart)
                msg = pgettext(
                    'Checkout warning',
                    'This voucher has expired. Please review your checkout.')
                messages.warning(request, msg)
                return redirect('checkout:summary')
        return view(request, cart)
    return func


@require_POST
@get_or_empty_db_cart(Cart.objects.for_display())
def remove_voucher_view(request, cart):
    """Clear the discount and remove the voucher."""
    next_url = request.GET.get('next', request.META['HTTP_REFERER'])
    remove_voucher_from_cart(cart)
    return redirect(next_url)
