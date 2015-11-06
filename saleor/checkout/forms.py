from django import forms
from django.utils.translation import ugettext_lazy as _


class CopyShippingAddressForm(forms.Form):

    billing_same_as_shipping = forms.BooleanField(
        initial=True, required=False, label=_('Change billing address'))


class DeliveryForm(forms.Form):

    method = forms.ChoiceField(label=_('Shipping method'),
                               widget=forms.RadioSelect)

    def __init__(self, delivery_choices, *args, **kwargs):
        super(DeliveryForm, self).__init__(*args, **kwargs)
        method_field = self.fields['method']
        method_field.choices = delivery_choices
        if len(delivery_choices) == 1:
            method_field.initial = delivery_choices[0][1]


class AnonymousEmailForm(forms.Form):

    email = forms.EmailField()
