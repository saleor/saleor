from django import forms
from django.utils.translation import pgettext_lazy

from ...shipping.models import ShippingMethod, ShippingMethodCountry


class ShippingMethodForm(forms.ModelForm):

    class Meta:
        model = ShippingMethod
        exclude = []
        labels = {
            'name': pgettext_lazy(
                'Shipping method name', 'Name'),
            'description': pgettext_lazy(
                'Description', 'Description')}


class ShippingMethodCountryForm(forms.ModelForm):

    class Meta:
        model = ShippingMethodCountry
        exclude = []
        widgets = {'shipping_method': forms.widgets.HiddenInput()}
        labels = {
            'country_code': pgettext_lazy(
                'Country code', 'Country code'),
            'shipping_method': pgettext_lazy(
                'Shipping method', 'Shipping method'),
            'price': pgettext_lazy(
                'Price', 'Price')}
