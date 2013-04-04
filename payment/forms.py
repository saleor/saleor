from .fields import CreditCardNumberField
from authorizenet.fields import CreditCardExpiryField
from django import forms
from django.core import validators
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

CVV_VALIDATOR = validators.RegexValidator('^[0-9]{1,4}$',
                                          _('Enter a valid security number.'))


class PaymentForm(forms.Form):

    name = forms.CharField(label=_('Name on Credit Card'), max_length=128)
    number = CreditCardNumberField(label=_('Card Number'), max_length=32,
                                      required=True)
    expiration = CreditCardExpiryField()
    cvv2 = forms.CharField(validators=[CVV_VALIDATOR], required=False,
                              label=_('CVV2 Security Number'), max_length=4)


class PaymentMethodsForm(forms.Form):

    CHOICES = [(key, key.title()) for key in settings.PAYMENT_VARIANTS.keys()]
    method = forms.ChoiceField(choices=CHOICES)


class PaypalForm(forms.Form):

    invoice = forms.IntegerField()
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    city = forms.CharField(required=False)
    zip = forms.CharField(required=False)
    country = forms.CharField(required=False)
    amount = forms.DecimalField()
    currency_code = forms.CharField()
    notify_url = forms.CharField(required=False)
    business = forms.EmailField()
    cmd = forms.CharField(initial='_cart')
    upload = forms.CharField(initial='1')
    charset = forms.CharField(initial='utf-8')
