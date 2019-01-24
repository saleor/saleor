from django import forms
from django.utils.translation import pgettext_lazy

from ... import ChargeStatus


class DummyPaymentForm(forms.Form):
    charge_status = forms.ChoiceField(
        label=pgettext_lazy('Payment status form field', 'Payment status'),
        choices=ChargeStatus.CHOICES, initial=ChargeStatus.NOT_CHARGED,
        widget=forms.RadioSelect)

    def get_payment_token(self):
        """Return selected charge status instead of token for testing only.
        Gateways used for production should return an actual token instead."""
        charge_status = self.cleaned_data['charge_status']
        return charge_status
