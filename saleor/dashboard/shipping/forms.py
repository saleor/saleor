from django import forms
from django.utils.translation import pgettext_lazy

from ...shipping.models import ShippingMethod, ShippingMethodCountry


class ShippingMethodForm(forms.ModelForm):

    class Meta:
        model = ShippingMethod
        exclude = []
        labels = {
            'name': pgettext_lazy(
                'Shipping  method form label', 'Shipping method')
            'description': pgettext_lazy(
                'Shipping  method form label', 'Method description')}


class ShippingMethodCountryForm(forms.ModelForm):

    class Meta:
        model = ShippingMethodCountry
        exclude = []
        widgets = {'shipping_method': forms.widgets.HiddenInput()}
        labels = {
            'country_code': pgettext_lazy(
                'Shipping  method country form label', 'Country code'),
            'shipping_method': pgettext_lazy(
                'Shipping  method country form label', 'Shipping method'),
            'price': pgettext_lazy(
                'Shipping  method country form label', 'Price')}
