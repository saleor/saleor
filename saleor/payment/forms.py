from django import forms
from .models import PaymentMethod
from ..payment import TransactionType

class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['variant', 'is_active', 'total', 'charge_status']

    def authorize_payment(self):
        self.instance.transactions.create(
            amount=self.instance.total,
            transaction_type=TransactionType.AUTH,
            gateway_response={},
            is_success=True)
