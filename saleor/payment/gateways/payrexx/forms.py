from typing import Dict

from django import forms
from django.forms.widgets import HiddenInput
from django.utils.translation import pgettext_lazy

from ...interface import PaymentData
from .utils import create_payrexx_link

CHECKOUT_DESCRIPTION = pgettext_lazy(
    "Payrex payment gateway description", "Total payment"
)


class PayrexxPaymentForm(forms.Form):
    payrexxHash = forms.CharField(required=True, widget=HiddenInput)
    paymentLinkId = forms.CharField(required=True, widget=HiddenInput)

    def __init__(self,
                 payment_information: PaymentData,
                 gateway_params: Dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        payment_link = create_payrexx_link(payment_information, gateway_params)
        self.payrexxLink = payment_link['link']
        self.fields['payrexxHash'].initial = payment_link['hash']
        self.fields['paymentLinkId'].initial = payment_link['id']

    def get_payment_token(self):
        if self.cleaned_data:
            return self.cleaned_data["payrexxHash"] + ':'\
                + self.cleaned_data['paymentLinkId']
        return 'empty'
