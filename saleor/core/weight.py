from django import forms
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import pgettext_lazy
from measurement.measures import Mass


def zero_weight():
    """Function used as a model's default."""
    return Mass(kg=0)


class MassUnits:
    KILOGRAM = 'kg'
    POUND = 'lb'
    OUNCE = 'oz'
    GRAM = 'g'

    CHOICES = [
        (KILOGRAM, pgettext_lazy('Kilogram mass unit symbol', 'kg')),
        (POUND, pgettext_lazy('Pound mass unit symbol', 'lb')),
        (OUNCE, pgettext_lazy('Ounce mass unit symbol', 'oz')),
        (GRAM, pgettext_lazy('Gram mass unit symbol', 'g'))]

    dict_choices = dict(CHOICES)


class WeightInput(forms.TextInput):
    template = 'dashboard/shipping/weight_widget.html'
    input_type = 'number'

    def __init__(
            self, unit_choice=settings.DEFAULT_WEIGHT_UNITS[0][0],
            *args, **kwargs):
        self.unit_choice = unit_choice
        super().__init__(*args, **kwargs)

    def format_value(self, value):
        if isinstance(value, Mass):
            return value.value
        return value

    def render(self, name, value, attrs=None):
        widget = super().render(name, value, attrs=attrs)
        return render_to_string(self.template, {
            'widget': widget, 'value': value, 'unit': self.unit_choice})


class WeightField(forms.DecimalField):
    def __init__(
            self, unit_choice=settings.DEFAULT_WEIGHT_UNITS[0][0],
            widget=WeightInput, *args, **kwargs):
        self.unit_choice = unit_choice
        if isinstance(widget, type):
            widget = widget(
                unit_choice=self.unit_choice,
                attrs={'type': 'number', 'step': 'any'})
        super().__init__(*args, widget=widget, **kwargs)

    def to_python(self, value):
        value = super().to_python(value)
        if value is None:
            return value
        return Mass(**{self.unit_choice: value})

    def validate(self, mass):
        if mass in self.empty_values:
            super().validate(mass)
            return mass
        elif not isinstance(mass, Mass):
            raise Exception('%r is not a valid mass.' % (mass,))
        elif mass.unit != self.unit_choice:
            raise forms.ValidationError(
                'Invalid unit_choice: %r (expected %r).' % (
                    mass.unit, self.unit_choice))
        elif mass.value < 0:
            raise forms.ValidationError(
                'Weight should be larger or equal 0 %(unit)s.' % {
                    'unit': self.unit_choice})

    def clean(self, value):
        value = self.to_python(value)
        self.validate(value)
        return value
