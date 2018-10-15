from django import forms
from django.conf import settings
from django.utils.translation import pgettext_lazy

from ..account.forms import SignupForm
from ..payment import PaymentMethodChargeStatus, can_be_voided
from ..payment.models import PaymentMethod
from .models import Order


class PaymentMethodsForm(forms.Form):
    method = forms.ChoiceField(
        label=pgettext_lazy('Payment methods form label', 'Method'),
        choices=settings.CHECKOUT_PAYMENT_CHOICES, widget=forms.RadioSelect,
        initial=settings.CHECKOUT_PAYMENT_CHOICES[0][0])


class PaymentDeleteForm(forms.Form):
    payment_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order')
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        payment_id = cleaned_data.get('payment_id')
        payment = PaymentMethod.objects.filter(is_active=True).first(
            id=payment_id)
        if not payment:
            self._errors['number'] = self.error_class([
                pgettext_lazy(
                    'Payment delete form error', 'Payment does not exist')])
        elif not can_be_voided(payment):
            self._errors['number'] = self.error_class([
                pgettext_lazy(
                    'Payment delete form error',
                    'Payment cannot be cancelled.')])
        else:
            cleaned_data['payment'] = payment
        return cleaned_data

    def save(self):
        payment = self.cleaned_data['payment']
        payment.void()


class PasswordForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget = forms.HiddenInput()


class CustomerNoteForm(forms.ModelForm):
    customer_note = forms.CharField(
        max_length=250, required=False, strip=True, label=False,
        widget=forms.Textarea({'rows': 3}))

    class Meta:
        model = Order
        fields = ['customer_note']
