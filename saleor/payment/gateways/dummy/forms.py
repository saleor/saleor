from ...forms import PaymentForm
from django import forms
from django.utils.translation import pgettext_lazy

from ... import ChargeStatus


class DummyPaymentForm(PaymentForm):
    charge_status = forms.ChoiceField(
        label=pgettext_lazy('Payment status form field', 'Payment status'),
        choices=ChargeStatus.CHOICES, initial=ChargeStatus.NOT_CHARGED,
        widget=forms.RadioSelect)


    def process_payment(self):
        # Dummy provider requires no real token
        fake_token = self.gateway.get_client_token(**self.gateway_params)
        self.payment.authorize(fake_token)
        charge_status = self.cleaned_data['charge_status']
        if charge_status == ChargeStatus.NOT_CHARGED:
            return
        self.payment.capture()
        if charge_status == ChargeStatus.FULLY_REFUNDED:
            self.payment.refund()
        return self.payment
