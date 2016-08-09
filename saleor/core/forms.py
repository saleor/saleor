from django import forms
from django.conf import settings
from django_countries import countries
from django_countries.fields import LazyTypedChoiceField

from ..shipping.models import (ShippingCountryBase, ANY_COUNTRY_DISPLAY,
                               ANY_COUNTRY)


class CurrencyForm(forms.Form):
    CURRENCY_CHOICES = (
        (currency, currency) for currency in settings.AVAILABLE_CURRENCIES
    )
    currency = forms.ChoiceField(choices=CURRENCY_CHOICES)


class StyleGuideForm(forms.Form):
    CHOICES = (
        ('red', 'Red'),
        ('blue', 'Blue'),
        ('yellow', 'Yellow'),
        ('black', 'Black'))

    input_label = forms.CharField(help_text='Help text')
    number_input = forms.IntegerField(initial=100)
    text_area = forms.CharField(widget=forms.Textarea)
    select_menu = forms.ChoiceField(choices=CHOICES)
    input_groups = forms.CharField()
    radio_buttons = forms.ChoiceField(
        choices=CHOICES, widget=forms.RadioSelect)
    checkboxes = forms.MultipleChoiceField(
        choices=CHOICES, widget=forms.CheckboxSelectMultiple)


class SelectCountryForm(forms.Form):
    country_code = LazyTypedChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super(SelectCountryForm, self).__init__(*args, **kwargs)
        shipping_available = set(
            [obj.country_code for obj in ShippingCountryBase.objects.all()
             if obj.country_code])
        choices = [(ANY_COUNTRY, ANY_COUNTRY_DISPLAY)]
        choices += [(country_code, dict(countries)[country_code])
                    for country_code in shipping_available]
        self.fields['country_code'].choices = choices
