import uuid

from django import forms
from django.utils.translation import pgettext_lazy

from ... import ChargeStatus


class DummyPaymentForm(forms.Form):
    charge_status = forms.ChoiceField(
        label=pgettext_lazy('Payment status form field', 'Payment status'),
        choices=ChargeStatus.CHOICES, initial=ChargeStatus.NOT_CHARGED,
        widget=forms.RadioSelect)

    def __init__(self, payment_information, gateway_params, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_payment_token(self):
        return str(uuid.uuid4())
