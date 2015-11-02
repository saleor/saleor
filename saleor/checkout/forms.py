from django import forms
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import ugettext_lazy as _

from ..userprofile.forms import AddressForm


class CopyShippingAddressForm(forms.Form):
    shipping_same_as_billing = forms.BooleanField(initial=True, required=False)


class ShippingAddressForm(AddressForm):
    pass


class DeliveryForm(forms.Form):

    method = forms.ChoiceField(label=_('Shipping method'))

    def __init__(self, delivery_choices, *args, **kwargs):
        super(DeliveryForm, self).__init__(*args, **kwargs)
        method_field = self.fields['method']
        method_field.choices = delivery_choices
        if len(delivery_choices) == 1:
            method_field.initial = delivery_choices[0][1]
            # method_field.widget = forms.HiddenInput()


class AnonymousEmailForm(forms.Form):

    email = forms.EmailField()
