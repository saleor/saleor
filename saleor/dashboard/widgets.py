from __future__ import unicode_literals
from django_filters.widgets import RangeWidget
from django_prices.widgets import PriceInput

from django import forms
from django.conf import settings


class DateRangeWidget(RangeWidget):
    def __init__(self, attrs=None):
        widgets = (forms.DateInput, forms.DateInput)
        super(RangeWidget, self).__init__(widgets, attrs)


class PriceRangeWidget(RangeWidget):
    def __init__(self, attrs=None):
        self.currency = getattr(settings, 'DEFAULT_CURRENCY')
        widgets = (PriceInput(self.currency), PriceInput(self.currency))
        super(RangeWidget, self).__init__(widgets, attrs)
