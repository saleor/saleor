from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import pgettext_lazy


class BraintreePaymentForm(forms.Form):
    amount = forms.DecimalField()

    # Unique transaction identifier returned by Braintree
    # for testing in the sandbox mode please refer to
    # https://developers.braintreepayments.com/reference/general/testing/python#nonces-representing-cards
    # as it's values should be hardcoded to simulate each payment gateway
    # response
    payment_method_nonce = forms.CharField()

    def __init__(self, payment_information, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.payment_information = payment_information
        self.fields['amount'].initial = payment_information['amount']

    def clean(self):
        cleaned_data = super().clean()
        # Amount is sent client-side
        # authorizing different amount than payments' total could happen only
        # when manually adjusting the template value as we do not allow
        # partial-payments at this moment, error is returned instead.
        amount = cleaned_data.get('amount')
        if amount and amount != self.payment_information['amount']:
            msg = pgettext_lazy(
                'payment error',
                'Unable to process transaction. Please try again in a moment')
            raise ValidationError(msg)
        return cleaned_data

    def get_payment_token(self):
        return self.cleaned_data['payment_method_nonce']
