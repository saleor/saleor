from django import forms
from django.conf import settings
from django.forms import Textarea, TextInput
from django_filters import widgets
from django_prices.widgets import MoneyInput

from ..account.widgets import PhonePrefixWidget as StorefrontPhonePrefixWidget


class DateRangeWidget(widgets.DateRangeWidget):
    def __init__(self, attrs=None):
        date_widgets = (forms.DateInput, forms.DateInput)
        # pylint: disable=bad-super-call
        super(widgets.RangeWidget, self).__init__(date_widgets, attrs)


class MoneyRangeWidget(widgets.RangeWidget):
    def __init__(self, attrs=None):
        self.currency = getattr(settings, 'DEFAULT_CURRENCY')
        money_widgets = (MoneyInput(self.currency), MoneyInput(self.currency))
        # pylint: disable=bad-super-call
        super(widgets.RangeWidget, self).__init__(money_widgets, attrs)


class PhonePrefixWidget(StorefrontPhonePrefixWidget):
    template_name = 'dashboard/order/widget/phone_prefix_widget.html'


class RichTextEditorWidget(Textarea):
    """A WYSIWYG editor widget using medium-editor."""

    def __init__(self, attrs=None):
        default_attrs = {'class': 'rich-text-editor'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class CharsLeftWidget(TextInput):
    """Displays number of characters left on the right side of the label,
    requires different rendering on the frontend.
    """
