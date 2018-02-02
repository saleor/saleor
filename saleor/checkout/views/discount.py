from datetime import date
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext
from django.views.decorators.http import require_POST

from ...discount.forms import CheckoutDiscountForm
from ...discount.models import Voucher
from ..core import load_checkout


def add_voucher_form(view):
    """Decorate a view injecting a voucher form and handling its submission."""
    @wraps(view)
    def func(request, checkout):
        prefix = 'discount'
        data = {k: v for k, v in request.POST.items() if k.startswith(prefix)}
        voucher_form = CheckoutDiscountForm(
            data or None, checkout=checkout, prefix=prefix)
        if voucher_form.is_bound:
            if voucher_form.is_valid():
                voucher_form.apply_discount()
                next_url = request.GET.get(
                    'next', request.META['HTTP_REFERER'])
                return redirect(next_url)
            else:
                del checkout.discount
                del checkout.voucher_code
                # if only discount form was used we clear post for other forms
                request.POST = {}
        else:
            checkout.recalculate_discount()
        response = view(request, checkout)
        if isinstance(response, TemplateResponse):
            voucher = voucher_form.initial.get('voucher')
            response.context_data['voucher_form'] = voucher_form
            response.context_data['voucher'] = voucher
        return response
    return func


def validate_voucher(view):
    """Decorate a view making it check whether a discount voucher is valid.

    If the voucher is invalid it will be removed and the user will be
    redirected to the checkout summary view.
    """
    @wraps(view)
    def func(request, checkout, cart):
        if checkout.voucher_code:
            try:
                Voucher.objects.active(date=date.today()).get(
                    code=checkout.voucher_code)
            except Voucher.DoesNotExist:
                del checkout.voucher_code
                checkout.recalculate_discount()
                msg = pgettext(
                    'Checkout warning',
                    'This voucher has expired. Please review your checkout.')
                messages.warning(request, msg)
                return redirect('checkout:summary')
        return view(request, checkout, cart)
    return func


@require_POST
@load_checkout
def remove_voucher_view(request, checkout, cart):
    """Clear the discount and remove the voucher."""
    next_url = request.GET.get('next', request.META['HTTP_REFERER'])
    del checkout.discount
    del checkout.voucher_code
    return redirect(next_url)
