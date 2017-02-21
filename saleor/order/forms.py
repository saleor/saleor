from django import forms
from django.conf import settings
from django.utils.translation import pgettext_lazy
from payments import PaymentStatus

from .models import Payment
from ..registration.forms import SignupForm


class PaymentMethodsForm(forms.Form):
    method = forms.ChoiceField(
        label=pgettext_lazy('Payment methods form label', 'Method'),
        choices=settings.CHECKOUT_PAYMENT_CHOICES, widget=forms.RadioSelect,
        initial=settings.CHECKOUT_PAYMENT_CHOICES[0][0])


class PaymentDeleteForm(forms.Form):
    payment_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order')
        super(PaymentDeleteForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(PaymentDeleteForm, self).clean()
        payment_id = cleaned_data.get('payment_id')
        waiting_payments = self.order.payments.filter(
            status=PaymentStatus.WAITING)
        try:
            payment = waiting_payments.get(id=payment_id)
        except Payment.DoesNotExist:
            self._errors['number'] = self.error_class([
                pgettext_lazy(
                    'Payment delete form error',
                    'Payment does not exist')])
        else:
            cleaned_data['payment'] = payment
        return cleaned_data

    def save(self):
        payment = self.cleaned_data['payment']
        payment.status = PaymentStatus.REJECTED
        payment.save()


class PasswordForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super(PasswordForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget = forms.HiddenInput()
