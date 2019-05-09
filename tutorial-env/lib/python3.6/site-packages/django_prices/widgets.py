from django import forms
from django.template.loader import render_to_string
from prices import Money

__all__ = ['MoneyInput']


class MoneyInput(forms.TextInput):
    template = 'prices/widget.html'
    input_type = 'number'

    def __init__(self, currency, *args, **kwargs):
        self.currency = currency
        super(MoneyInput, self).__init__(*args, **kwargs)

    def format_value(self, value):
        if isinstance(value, Money):
            return value.amount
        return value

    def render(self, name, value, attrs=None, renderer=None):
        widget = super(MoneyInput, self).render(name, value, attrs=attrs, renderer=renderer)
        return render_to_string(self.template, {
            'widget': widget, 'value': value, 'currency': self.currency})
