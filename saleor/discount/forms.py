from django import forms
from django.utils.translation import pgettext_lazy

from .models import Voucher, NotApplicable


class VoucherField(forms.ModelChoiceField):

    default_error_messages = {
        'invalid_choice': pgettext_lazy(
            'voucher', pgettext_lazy(
                'voucher', 'Discount code incorrect or expired')),
    }


class CheckoutDiscountForm(forms.Form):

    voucher = VoucherField(
        queryset=Voucher.objects.active(), to_field_name='code',
        label=pgettext_lazy('voucher', 'Gift card or discount code'),
        widget=forms.TextInput)

    def __init__(self, *args, **kwargs):
        self.checkout = kwargs.pop('checkout')
        initial = kwargs.get('initial', {})
        if 'voucher' not in initial:
            initial['voucher'] = self.checkout.voucher_code
        super(CheckoutDiscountForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(CheckoutDiscountForm, self).clean()
        if 'voucher' in cleaned_data:
            voucher = cleaned_data['voucher']
            try:
                discount = voucher.get_discount_for_checkout(self.checkout)
                cleaned_data['discount'] = discount
            except NotApplicable as e:
                self.add_error('voucher', str(e))
        return cleaned_data
