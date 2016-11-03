from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext

from ...discount.forms import CheckoutDiscountForm
from ...discount.models import Voucher


def add_voucher_form(view):
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
    @wraps(view)
    def func(request, checkout, cart):
        if checkout.voucher_code:
            try:
                Voucher.objects.active().get(code=checkout.voucher_code)
            except Voucher.DoesNotExist:
                del checkout.voucher_code
                checkout.recalculate_discount()
                msg = pgettext(
                    'checkout warning',
                    'This voucher has expired. Please review your checkout.')
                messages.warning(request, msg)
                return redirect('checkout:summary')
        return view(request, checkout, cart)
    return func


def remove_voucher_view(request, checkout, cart):
    next_url = request.GET.get('next', request.META['HTTP_REFERER'])
    del checkout.discount
    del checkout.voucher_code
    return redirect(next_url)
