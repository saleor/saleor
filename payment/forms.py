from .fields import CreditCardExpirationYearField, CreditCardNumberField
from django import forms
from django.core import validators
from django.utils.translation import ugettext_lazy as _
from payment.fields import CreditCardExpirationMonthField
from datetime import date

CVV_VALIDATOR = validators.RegexValidator('^[0-9]{1,4}$',
                                          _('Enter a valid security number.'))


class PaymentForm(forms.Form):
    cc_name = forms.CharField(label=_('Name on Credit Card'), max_length=128)
    cc_number = CreditCardNumberField(label=_('Card Number'), max_length=32,
                                      required=True)
    cc_expiration_year = CreditCardExpirationYearField(label=_('Exp. date'))
    cc_expiration_month = CreditCardExpirationMonthField(label=_('Exp. date'))
    cc_cvv2 = forms.CharField(validators=[CVV_VALIDATOR], required=False,
                              label=_('CVV2 Security Number'), max_length=4)

    def clean(self):
        cleaned_data = super(PaymentForm, self).clean()
        month = cleaned_data.get('cc_expiration_month')
        year = cleaned_data.get('cc_expiration_year')
        try:
            expiration = date(int(year), int(month), 01)
        except ValueError:
            raise forms.ValidationError(_('Enter a valid value.'))
        if expiration < date.today():
                raise forms.ValidationError(_('This credit card has '
                                              'already expired'))
        return cleaned_data
