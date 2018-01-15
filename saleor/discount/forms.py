from datetime import date

from django import forms
from django.utils.encoding import smart_text
from django.utils.translation import pgettext_lazy

from .models import NotApplicable, Voucher


class VoucherField(forms.ModelChoiceField):

    default_error_messages = {
        'invalid_choice': pgettext_lazy(
            'voucher', pgettext_lazy(
                'Voucher form error', 'Discount code incorrect or expired')),
    }


class CheckoutDiscountForm(forms.Form):

    voucher = VoucherField(
        queryset=Voucher.objects.none(),
        to_field_name='code',
        help_text=pgettext_lazy(
            'Checkout discount form label for voucher field',
            'Gift card or discount code'),
        widget=forms.TextInput)

    def __init__(self, *args, **kwargs):
        self.checkout = kwargs.pop('checkout')
        initial = kwargs.get('initial', {})
        if 'voucher' not in initial:
            initial['voucher'] = self.checkout.voucher_code
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)
        self.fields['voucher'].queryset = Voucher.objects.active(
            date=date.today())

    def clean(self):
        cleaned_data = super().clean()
        if 'voucher' in cleaned_data:
            voucher = cleaned_data['voucher']
            try:
                discount = voucher.get_discount_for_checkout(self.checkout)
                cleaned_data['discount'] = discount
            except NotApplicable as e:
                self.add_error('voucher', smart_text(e))
        return cleaned_data

    def apply_discount(self):
        discount = self.cleaned_data['discount']
        voucher = self.cleaned_data['voucher']
        self.checkout.discount = discount
        self.checkout.voucher_code = voucher.code
