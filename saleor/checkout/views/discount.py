from functools import wraps
from django.shortcuts import redirect

from ...discount.forms import GetVoucherForm


def add_voucher_form(view):
    @wraps(view)
    def func(request, checkout):
        voucher = None
        initial = {'voucher': voucher}
        voucher_form = GetVoucherForm(
            request.POST or None, prefix='discount', initial=initial)
        template_response = view(request, checkout)
        template_response.context_data['voucher_form'] = voucher_form
        template_response.context_data['voucher'] = voucher
        return template_response
    return func


def apply_voucher_view(request, checkout):
    voucher_form = GetVoucherForm(request.POST or None, prefix='discount')
    next_url = request.GET.get('next', request.META['HTTP_REFERER'])
    if voucher_form.is_valid():
        voucher = voucher_form.cleaned_data['voucher']
    return redirect(next_url)

