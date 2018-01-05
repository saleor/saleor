from django import forms
from django.utils.translation import pgettext_lazy

from ...shipping.models import ShippingMethod, ShippingMethodCountry


class ShippingMethodForm(forms.ModelForm):

    class Meta:
        model = ShippingMethod
        exclude = []
        labels = {
            'name': pgettext_lazy(
                'Item name', 'Name'),
            'description': pgettext_lazy(
                'Description', 'Description')}


class ShippingMethodCountryForm(forms.ModelForm):

    class Meta:
        model = ShippingMethodCountry
        exclude = []
        widgets = {'shipping_method': forms.widgets.HiddenInput()}
        labels = {
            'country_code': pgettext_lazy(
                'List of countries', 'Country'),
            'price': pgettext_lazy(
                'Currency amount', 'Price')}
