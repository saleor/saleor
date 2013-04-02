from .fields import CreditCardExpirationYearField, CreditCardNumberField
from authorizenet.fields import CreditCardExpiryField
from datetime import date
from django import forms
from django.core import validators
from django.utils.translation import ugettext_lazy as _
from payment.fields import CreditCardExpirationMonthField

CVV_VALIDATOR = validators.RegexValidator('^[0-9]{1,4}$',
                                          _('Enter a valid security number.'))


class PaymentForm(forms.Form):
    name = forms.CharField(label=_('Name on Credit Card'), max_length=128)
    number = CreditCardNumberField(label=_('Card Number'), max_length=32,
                                      required=True)
    expiration = CreditCardExpiryField()
    cvv2 = forms.CharField(validators=[CVV_VALIDATOR], required=False,
                              label=_('CVV2 Security Number'), max_length=4)
