from django import forms
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import ugettext_lazy as _

from ..order.models import DigitalDeliveryGroup
from ..userprofile.forms import AddressForm


class ShippingForm(AddressForm):

    use_billing = forms.BooleanField(initial=True)


class DigitalDeliveryForm(forms.ModelForm):

    class Meta:
        model = DigitalDeliveryGroup
        fields = ['email']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) or AnonymousUser()
        super(DigitalDeliveryForm, self).__init__(*args, **kwargs)
        email = self.fields['email']
        email.required = True
        if user.is_authenticated():
            email.initial = user.email


class DeliveryForm(forms.Form):

    method = forms.ChoiceField(label=_('Shipping method'))

    def __init__(self, delivery_choices, *args, **kwargs):
        super(DeliveryForm, self).__init__(*args, **kwargs)
        method_field = self.fields['method']
        method_field.choices = delivery_choices
        if len(delivery_choices) == 1:
            method_field.initial = delivery_choices[0][1]
            method_field.widget = forms.HiddenInput()


class AnonymousEmailForm(forms.Form):

    email = forms.EmailField()
