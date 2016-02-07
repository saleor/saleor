from functools import wraps

from django.shortcuts import redirect
from django.template.response import TemplateResponse

from ...discount.forms import CheckoutDiscountForm


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


def remove_voucher_view(request, checkout):
    next_url = request.GET.get('next', request.META['HTTP_REFERER'])
    del checkout.discount
    del checkout.voucher_code
    return redirect(next_url)
