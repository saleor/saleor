from django import forms
from django.utils.translation import pgettext_lazy

from .models import Voucher


class GetVoucherForm(forms.Form):

    voucher = forms.ModelChoiceField(
        queryset=Voucher.objects.all(), to_field_name='code',
        label=pgettext_lazy('voucher', 'Gift card or discount code'),
        widget=forms.TextInput)
