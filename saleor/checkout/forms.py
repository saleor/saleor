from django import forms
from django.contrib.auth.models import AnonymousUser
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.encoding import smart_text
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


class DeliveryField(forms.ChoiceField):

    _methods = None

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        for method in self._methods:
            if method.name == value:
                return method
        error_message = self.error_messages['invalid_choice']
        raise ValidationError(error_message % {'value': value})

    def valid_value(self, value):
        return value in self._methods

    @property
    def methods(self):
        return self._methods

    @methods.setter
    def methods(self, value):
        self._methods = value
        self.choices = [(method.name, smart_text(method))
                        for method in self._methods]


class DeliveryForm(forms.Form):

    method = DeliveryField(label=_('Shipping method'))

    def __init__(self, delivery_methods, *args, **kwargs):
        super(DeliveryForm, self).__init__(*args, **kwargs)
        method_field = self.fields['method']
        method_field.methods = delivery_methods
        if len(delivery_methods) == 1:
            method_field.initial = delivery_methods[0]
            method_field.widget = forms.HiddenInput()


class AnonymousEmailForm(forms.Form):

    email = forms.EmailField()
