from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import pgettext_lazy

from . import ChargeStatus, TransactionType, get_provider
from .models import Payment
from .utils import gateway_authorize, gateway_capture, gateway_refund


def get_form_for_payment(payment):
    if payment.variant == settings.DUMMY:
        return DummyPaymentForm
    elif payment.variant == settings.BRAINTREE:
        return BraintreePaymentForm
    raise ValueError('Unknown payment provider')


class DummyPaymentForm(forms.Form):
    charge_status = forms.ChoiceField(
        label=pgettext_lazy('Payment status form field', 'Payment status'),
        choices=ChargeStatus.CHOICES, initial=ChargeStatus.NOT_CHARGED,
        widget=forms.RadioSelect)

    def __init__(self, instance, *args, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)

    def process_payment(self):
        # FIXME add tests
        provider, provider_params = get_provider(self.instance.variant)
        transaction_token = provider.get_transaction_token(**provider_params)
        charge_status = self.cleaned_data['charge_status']
        self.instance.authorize(transaction_token)
        if charge_status == ChargeStatus.NOT_CHARGED:
            return
        self.instance.capture()
        if charge_status == ChargeStatus.FULLY_REFUNDED:
            self.instance.refund()
        return self.instance


class BraintreePaymentForm(forms.Form):
    amount = forms.DecimalField()

    # Unique transaction identifier returned by Braintree
    # for testing in the sandbox please refer to
    # https://developers.braintreepayments.com/reference/general/testing/python#nonces-representing-cards
    # as it's values should be hardcoded to simulate each payment-gateway
    # response
    payment_method_nonce = forms.CharField()

    def __init__(self, instance, *args, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        self.fields['amount'].initial = self.instance.total
        #FIXME if environment is Sandbox, we could provide couple of predefined
        # nounces for easier testing

    def clean(self):
        cleaned_data = super().clean()
        # Amount is sent client-side
        # authorizing different amount than payments' total could happen only
        # when manually adjusting the template value as we do not allow
        # partial-payments at this moment, error is returned instead.
        amount = cleaned_data.get('amount')
        if amount and amount != self.instance.total:
            msg = pgettext_lazy(
                'payment error',
                'Unable to process transaction. Please try again in a moment')
            raise ValidationError(msg)
        return cleaned_data

    def process_payment(self):
        # FIXME add tests
        self.instance.authorize(self.cleaned_data['payment_method_nonce'])
        try:
            self.instance.capture(self.instance.total)
        except PaymentError as exc:
            # Void authorization if the capture failed
            self.instance.void()
            raise exc
        return self.instance
