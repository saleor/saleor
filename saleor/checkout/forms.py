from django import forms
from django.utils.translation import ugettext_lazy as _
from saleor.userprofile.models import Address


class AddressChoiceField(forms.ModelChoiceField):
    choice_values = []

    def validate(self, value):
        if value not in self.choice_values:
            return super(AddressChoiceField, self).validate(value)

    def to_python(self, value):
        if value in self.choice_values:
            return value
        else:
            return super(AddressChoiceField, self).to_python(value)

    def add_magic_choices(self, magic_choices, queryset):
        choices = list(queryset) if queryset else []
        self.choices = magic_choices + choices


class UserAddressesForm(forms.Form):
    address = AddressChoiceField(
        queryset=Address.objects.none(),
        widget=forms.RadioSelect)

    def __init__(self, queryset, possibilities, *args, **kwargs):
        super(UserAddressesForm, self).__init__(*args, **kwargs)
        address_field = self.fields['address']
        address_field.queryset = queryset if queryset else Address.objects.none()
        address_field.add_magic_choices(possibilities, queryset)
        address_field.choice_values = [value for value, label in possibilities]


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
