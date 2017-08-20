from __future__ import unicode_literals

from django import forms
from django.forms import inlineformset_factory

from ...shipping.models import ShippingMethod, ShippingMethodCountry


class ShippingMethodForm(forms.ModelForm):

    class Meta:
        model = ShippingMethod
        exclude = []


ShippingMethodCountryFormSet = inlineformset_factory(
    ShippingMethod, ShippingMethodCountry, fields=['country_code', 'price'],
    can_delete=True, extra=2, min_num=1, validate_min=True)
