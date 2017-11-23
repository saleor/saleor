from django_filters.widgets import RangeWidget
from django import forms


class DateRangeWidget(RangeWidget):
    def __init__(self, attrs=None):
        widgets = (forms.DateInput, forms.DateInput)
        super(RangeWidget, self).__init__(widgets, attrs)
