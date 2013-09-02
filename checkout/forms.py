from django import forms
from django.contrib.auth.models import AnonymousUser
from django.core import validators
from django.core.exceptions import ValidationError
from order.models import DigitalDeliveryGroup
from userprofile.forms import AddressForm


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
            print 'asd'
            email.initial = user.email


class DeliveryField(forms.ChoiceField):

    def __init__(self, methods, *args, **kwargs):
        self.methods = list(methods)
        choices = [(index, unicode(method)) for index, method in
                   enumerate(self.methods)]
        super(DeliveryField, self).__init__(choices, *args, **kwargs)

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        try:
            return self.methods[int(value)]
        except (IndexError, ValueError):
            raise ValidationError(
                self.error_messages['invalid_choice'] % {'value': value})

    def valid_value(self, value):
        return value in self.methods


class DeliveryForm(forms.Form):

    def __init__(self, delivery_methods, *args, **kwargs):
        super(DeliveryForm, self).__init__(*args, **kwargs)
        self.fields['method'] = DeliveryField(delivery_methods)


class AnonymousEmailForm(forms.Form):

    email = forms.EmailField()
