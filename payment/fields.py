from . import widgets
from django import forms
from django.core import validators
from django.utils.translation import ugettext_lazy as _
from datetime import datetime
from calendar import monthrange
import re


class CreditCardNumberField(forms.CharField):
    widget = widgets.CreditCardNumberWidget
    default_error_messages = {
        'invalid': _(u'Please enter a valid card number'),
    }

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.pop('max_length', 32)
        super(CreditCardNumberField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        cleaned = re.sub('[\s-]', '', value)
        if value and not cleaned:
            raise forms.ValidationError(self.error_messages['invalid'])
        return cleaned

    def validate(self, value):
        if value in validators.EMPTY_VALUES and self.required:
            raise forms.ValidationError(self.error_messages['required'])
        if value and not self.cart_number_checksum_validation(value):
            raise forms.ValidationError(self.error_messages['invalid'])

    def cart_number_checksum_validation(self, number):
        digits = []
        even = False
        if not number.isdigit():
            return False
        for digit in reversed(number):
            digit = ord(digit) - ord('0')
            if even:
                digit = digit * 2
                if digit >= 10:
                    digit = digit % 10 + digit / 10
            digits.append(digit)
            even = not even
        return sum(digits) % 10 == 0 if digits else False


# Credit Card Expiry Fields from:
# http://www.djangosnippets.org/snippets/907/
class CreditCardExpiryWidget(forms.MultiWidget):
    """MultiWidget for representing credit card expiry date."""
    def decompress(self, value):
        if value:
            return [value.month, value.year]
        else:
            return [None, None]

    def format_output(self, rendered_widgets):
        html = u' / '.join(rendered_widgets)
        return u'<span style="white-space: nowrap">%s</span>' % html


# From https://github.com/zen4ever/django-authorizenet
class CreditCardExpiryField(forms.MultiValueField):
    EXP_MONTH = [(x, "%02d" % x) for x in xrange(1, 13)]
    EXP_YEAR = [(x, x) for x in xrange(datetime.today().year,
                                       datetime.today().year + 15)]

    default_error_messages = {
        'invalid_month': u'Enter a valid month.',
        'invalid_year': u'Enter a valid year.',
    }

    def __init__(self, *args, **kwargs):
        errors = self.default_error_messages.copy()
        if 'error_messages' in kwargs:
            errors.update(kwargs['error_messages'])

        fields = (
            forms.ChoiceField(
                choices=self.EXP_MONTH,
                error_messages={'invalid': errors['invalid_month']}),
            forms.ChoiceField(
                choices=self.EXP_YEAR,
                error_messages={'invalid': errors['invalid_year']}),
        )

        super(CreditCardExpiryField, self).__init__(fields, *args, **kwargs)
        self.widget = CreditCardExpiryWidget(widgets=[fields[0].widget,
                                                      fields[1].widget])

    def clean(self, value):
        exp = super(CreditCardExpiryField, self).clean(value)
        if datetime.today() > exp:
            raise forms.ValidationError(
                "The expiration date you entered is in the past.")
        return exp

    def compress(self, data_list):
        if data_list:
            if data_list[1] in forms.fields.EMPTY_VALUES:
                error = self.error_messages['invalid_year']
                raise forms.ValidationError(error)
            if data_list[0] in forms.fields.EMPTY_VALUES:
                error = self.error_messages['invalid_month']
                raise forms.ValidationError(error)
            year = int(data_list[1])
            month = int(data_list[0])
            # find last day of the month
            day = monthrange(year, month)[1]
            return datetime.date(year, month, day)
        return None
