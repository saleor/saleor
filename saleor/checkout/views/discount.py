from functools import wraps
from django.contrib import messages

from django.shortcuts import redirect
from django.template.response import TemplateResponse

from ...discount.forms import CheckoutDiscountForm
from ...discount.models import Voucher, NotApplicable


def add_voucher_form(view):
    @wraps(view)
    def func(request, checkout):
        voucher_form = CheckoutDiscountForm(
            None, checkout=checkout, prefix='discount')
        messages.get_messages(request)
        response = view(request, checkout)
        voucher_code = checkout.voucher_code
        if voucher_code:
            try:
                voucher = Voucher.objects.get(code=voucher_code)
            except Voucher.DoesNotExist:
                checkout.voucher_code = None
                voucher = None
        else:
            voucher = None
        if voucher is not None:
            try:
                checkout.discount = voucher.get_discount_for_checkout(checkout)
            except NotApplicable:
                del checkout.discount
                del checkout.voucher_code
        if isinstance(response, TemplateResponse):
            response.context_data['voucher_form'] = voucher_form
            response.context_data['voucher'] = voucher
        return response
    return func


def apply_voucher_view(request, checkout):
    voucher_form = CheckoutDiscountForm(
        request.POST or None, checkout=checkout, prefix='discount')
    next_url = request.GET.get('next', request.META['HTTP_REFERER'])
    if voucher_form.is_valid():
        discount = voucher_form.cleaned_data['discount']
        voucher = voucher_form.cleaned_data['voucher']
        checkout.discount = discount
        checkout.voucher_code = voucher.code
    else:
        for error in voucher_form.errors['voucher']:
            messages.error(request, error, extra_tags='discount')
    return redirect(next_url)


def remove_voucher_view(request, checkout):
    next_url = request.GET.get('next', request.META['HTTP_REFERER'])
    del checkout.discount
    del checkout.voucher_code
    return redirect(next_url)
