from django import forms
from django.conf import settings
from django.forms import Textarea
from django_filters.widgets import RangeWidget
from django_prices.widgets import MoneyInput

from ..account.widgets import (
    PhonePrefixWidget as StorefrontPhonePrefixWidget)


class DateRangeWidget(RangeWidget):
    def __init__(self, attrs=None):
        widgets = (forms.DateInput, forms.DateInput)
        # pylint: disable=bad-super-call
        super(RangeWidget, self).__init__(widgets, attrs)


class MoneyRangeWidget(RangeWidget):
    def __init__(self, attrs=None):
        self.currency = getattr(settings, 'DEFAULT_CURRENCY')
        widgets = (MoneyInput(self.currency), MoneyInput(self.currency))
        # pylint: disable=bad-super-call
        super(RangeWidget, self).__init__(widgets, attrs)


class PhonePrefixWidget(StorefrontPhonePrefixWidget):
    template_name = 'dashboard/order/widget/phone_prefix_widget.html'


class RichTextEditorWidget(Textarea):
    """A WYSIWYG editor widget using medium-editor."""

    def __init__(self, attrs=None):
        default_attrs = {'class': 'rich-text-editor'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class AceWidget(forms.Widget):
    HTML = 'html'
    JS = 'javascript'
    ALLOWED_MODS = [HTML, JS]
    template_name = 'dashboard/includes/_ace.html'

    def __init__(self, *args, **kwargs):
        self.mode = kwargs.pop('mode', 'html')
        super(AceWidget, self).__init__(*args, **kwargs)

    def get_context(self, name, value, attrs=None):
        return {
            'widget': {
                'name': name,
                'value': value,
                'attrs': attrs,
                'mode': self.mode
            }}
