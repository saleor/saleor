from . import widgets
from django import forms
from django.core import validators
from django.utils.translation import ugettext_lazy as _
import calendar
import datetime
import re
from datetime import datetime


def mod10(number):
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

class CreditCardNumberField(forms.CharField):
    widget =  widgets.CreditCardNumberWidget
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
        if value and not mod10(value):
            raise forms.ValidationError(self.error_messages['invalid'])

class CreditCardExpirationYearField(forms.ChoiceField):
    default_error_messages = {
        'expired': _(u'This credit card has already expired'),
    }

    def __init__(self, *args, **kwargs):
        current_year = datetime.now().year
        kwargs['choices'] = [(year, year) for year in
                             xrange(current_year, current_year + 11)]
        super(CreditCardExpirationYearField, self).__init__(*args, **kwargs)


class CreditCardExpirationMonthField(forms.ChoiceField):
    default_error_messages = {
        'expired': _(u'This credit card has already expired'),
    }

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = [(month, '%.2d' % (month, )) for month in
                             xrange(1, 13)]
        super(CreditCardExpirationMonthField, self).__init__(*args, **kwargs)


