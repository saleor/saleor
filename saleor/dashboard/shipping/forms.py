from __future__ import unicode_literals

from django import forms

from ...shipping.models import ShippingMethod, ShippingMethodCountry


class ShippingMethodForm(forms.ModelForm):

    class Meta:
        model = ShippingMethod
        exclude = []


class ShippingMethodCountryForm(forms.ModelForm):

    class Meta:
        model = ShippingMethodCountry
        exclude = []
        widgets = {'shipping_method': forms.widgets.HiddenInput()}
