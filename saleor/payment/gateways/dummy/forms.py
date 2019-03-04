from django import forms
from django.utils.translation import pgettext_lazy, ugettext_lazy as _

from ... import ChargeStatus


class DummyPaymentForm(forms.Form):
    charge_status = forms.ChoiceField(
        label=pgettext_lazy('Payment status form field', 'Payment status'),
        choices=ChargeStatus.CHOICES, initial=ChargeStatus.NOT_CHARGED,
        widget=forms.RadioSelect)

    def clean(self):
        cleaned_data = super(DummyPaymentForm, self).clean()

        # Partially refunded is not supported directly
        # since only last transaction of call_gateway will be processed
        charge_status = cleaned_data['charge_status']
        if charge_status in [
                ChargeStatus.PARTIALLY_CHARGED,
                ChargeStatus.PARTIALLY_REFUNDED]:
            raise forms.ValidationError(
                _('Setting charge status to {} directly '
                  'is not supported. Please use the dashboard to '
                  'refund partially.'.format(charge_status)),
                code='invalid_charge_status')

        return cleaned_data

    def get_payment_token(self):
        """Return selected charge status instead of token for testing only.
        Gateways used for production should return an actual token instead."""
        charge_status = self.cleaned_data['charge_status']
        return charge_status
