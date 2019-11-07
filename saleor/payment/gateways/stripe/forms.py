from django import forms

from ...interface import PaymentData

class StripePaymentForm(forms.Form):
    payment_method_id = forms.CharField()

    def __init__(self, payment_information: PaymentData, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.payment_information = payment_information

    def get_payment_token(self):
        return self.cleaned_data['payment_method_id']
