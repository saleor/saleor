"""In Saleor we are using 'weight' instead of a 'mass'.

For those of us who are earth-bound, weight is what we usually experience.
Mass is a theoretical construct.
Unless we are dealing with inertia and momentum, we are encountering
the attractive force between ourselves and the earth,
the isolated effects of mass alone being a little more esoteric.

So even though mass is more fundamental, most people think
in terms of weight.

In the end, it does not really matter unless you travel between
different planets.
"""
from decimal import Decimal

from django import forms
from django.contrib.sites.models import Site
from django.core.validators import MinValueValidator
from django.template.loader import render_to_string
from django.utils.translation import pgettext_lazy
from measurement.measures import Weight


class WeightUnits:
    KILOGRAM = 'kg'
    POUND = 'lb'
    OUNCE = 'oz'
    GRAM = 'g'

    CHOICES = [
        (KILOGRAM, pgettext_lazy('Kilogram weight unit symbol', 'kg')),
        (POUND, pgettext_lazy('Pound weight unit symbol', 'lb')),
        (OUNCE, pgettext_lazy('Ounce weight unit symbol', 'oz')),
        (GRAM, pgettext_lazy('Gram weight unit symbol', 'g'))]


def zero_weight():
    """Represent the zero weight value."""
    return Weight(kg=0)


def convert_weight(weight, unit):
    # Weight amount from the Weight instance can be retrived in serveral units
    # via its properties. eg. Weight(lb=10).kg
    converted_weight = getattr(weight, unit)
    return Weight(**{unit: converted_weight})


def get_default_weight_unit():
    site = Site.objects.get_current()
    return site.settings.default_weight_unit


class WeightInput(forms.TextInput):
    template = 'dashboard/shipping/weight_widget.html'
    input_type = 'number'

    def format_value(self, value):
        if isinstance(value, Weight):
            unit = get_default_weight_unit()
            if value.unit != unit:
                value = convert_weight(value, unit)
            return value.value
        return value

    def render(self, name, value, attrs=None, renderer=None):
        widget = super().render(name, value, attrs=attrs, renderer=renderer)
        unit = get_default_weight_unit()
        translated_unit = dict(WeightUnits.CHOICES)[unit]
        return render_to_string(
            self.template,
            {'widget': widget, 'value': value, 'unit': translated_unit})


class WeightField(forms.FloatField):
    def __init__(self, *args, widget=WeightInput, min_value=0, **kwargs):
        if isinstance(widget, type):
            widget = widget(attrs={'type': 'number', 'step': 'any'})
        super().__init__(*args, widget=widget, **kwargs)
        if min_value is not None:
            self.validators.append(MinValueValidator(min_value))

    def to_python(self, value):
        value = super().to_python(value)
        if value is None:
            return value
        unit = get_default_weight_unit()
        return Weight(**{unit: value})

    def validate(self, weight):
        if weight is None or weight in self.empty_values:
            super().validate(weight)
        else:
            unit = get_default_weight_unit()
            if not isinstance(weight, Weight):
                raise Exception(
                    '%r is not a valid weight.' % (weight,))
            if weight.unit != unit:
                raise forms.ValidationError(
                    'Invalid unit: %r (expected %r).' % (
                        weight.unit, unit))
            super().validate(weight.value)

    def clean(self, value):
        value = value_to_be_validated = self.to_python(value)
        self.validate(value_to_be_validated)
        if isinstance(value, Weight):
            value_to_be_validated = Decimal(value.value)
        # default decimal validators can be used for Weight's value only
        self.run_validators(value_to_be_validated)
        return value
