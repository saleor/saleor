from django import forms
from django.contrib.auth.models import AnonymousUser

from .models import Address, AddressBook


class AddressForm(forms.ModelForm):

    class Meta:
        model = Address


class AddressFormWithAlias(forms.ModelForm):

    class Meta:
        model = Address
        exclude = ['user']

    def clean(self):
        if Address.objects.filter(
            user=self.instance.user, alias=self.cleaned_data['alias']
        ).exclude(id=self.instance.id).exists():
            self._errors['alias'] = self.error_class(
                ['You are already using such alias for another address'])

        return self.cleaned_data


class UserAddressesForm(forms.Form):

    address = forms.ModelChoiceField(queryset=AddressBook.objects.none())

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', AnonymousUser()) or AnonymousUser()
        super(UserAddressesForm, self).__init__(*args, **kwargs)
        address = self.fields['address']
        if user.is_authenticated():
            address.queryset = AddressBook.objects.filter(user=user)
