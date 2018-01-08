from django import forms
from django.conf import settings
from django_filters.widgets import RangeWidget
from django_prices.widgets import PriceInput
from django.forms import Select, TextInput
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from phonenumbers import COUNTRY_CODE_TO_REGION_CODE


phone_prefixes = [
    ('+{}'.format(k), '+{}'.format(k)) for
    (k, v) in sorted(COUNTRY_CODE_TO_REGION_CODE.items())]


class DateRangeWidget(RangeWidget):
    def __init__(self, attrs=None):
        widgets = (forms.DateInput, forms.DateInput)
        super(RangeWidget, self).__init__(widgets, attrs)


class PriceRangeWidget(RangeWidget):
    def __init__(self, attrs=None):
        self.currency = getattr(settings, 'DEFAULT_CURRENCY')
        widgets = (PriceInput(self.currency), PriceInput(self.currency))
        super(RangeWidget, self).__init__(widgets, attrs)


class PhonePrefixWidget(PhoneNumberPrefixWidget):
    """
    Overwrite widget to use choices with tuple in a simple form of "+XYZ: +XYZ"
    Workaround for an issue:
    https://github.com/stefanfoulis/django-phonenumber-field/issues/82
    """

    template_name = 'dashboard/order/widget/phone-prefix-widget.html'

    def __init__(self, attrs=None):
        widgets = (Select(attrs=attrs, choices=phone_prefixes), TextInput())
        super(PhoneNumberPrefixWidget, self).__init__(widgets, attrs)
