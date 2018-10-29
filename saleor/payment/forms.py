from django import forms
from django.conf import settings


class PaymentForm(forms.Form):
    """Abstract Payment form that should be used as a base for every
    payment gateway implemented.
    """

    def __init__(self, payment, gateway, gateway_params, *args, **kwargs):
        self.payment = payment
        self.gateway = gateway
        self.gateway_params = gateway_params
        super().__init__(*args, **kwargs)

    def process_payment(self):
        raise NotImplementedError()
