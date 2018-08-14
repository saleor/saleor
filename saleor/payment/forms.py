from django import forms
from .models import PaymentMethod


class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['variant', 'is_active', 'total', 'charge_status']
