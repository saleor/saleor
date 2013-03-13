from .models import Address, AddressBook
from django import forms
from django.contrib.auth.models import AnonymousUser


class AddressForm(forms.ModelForm):

    class Meta:
        model = Address


class UserAddressesForm(forms.Form):

    address = forms.ModelChoiceField(queryset=AddressBook.objects.none())

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', AnonymousUser()) or AnonymousUser()
        super(UserAddressesForm, self).__init__(*args, **kwargs)
        address=self.fields['address']
        if user.is_authenticated():
            address.queryset = AddressBook.objects.filter(user=user)
