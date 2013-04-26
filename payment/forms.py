from django import forms
from django.conf import settings
from payments import get_payment_model
from django.utils.translation import ugettext_lazy as _

Payment = get_payment_model()


class PaymentMethodsForm(forms.Form):

    method = forms.ChoiceField(choices=settings.CHECKOUT_PAYMENT_CHOICES)


class PaymentDeledeForm(forms.Form):

    payment_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order')
        super(PaymentDeledeForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(PaymentDeledeForm, self).clean()
        payment_id = cleaned_data.get('payment_id')
        waiting_payments = self.order.payments.filter(status='waiting')
        try:
            payment = waiting_payments.get(id=payment_id)
        except Payment.DoesNotExist:
            self._errors['number'] = self.error_class(
                [_('Payment does not exist')])
        else:
            cleaned_data['payment'] = payment
        return cleaned_data

    def save(self):
        payment = self.cleaned_data['payment']
        payment.status = 'rejected'
        payment.save()
