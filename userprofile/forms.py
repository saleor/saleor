from .models import Address
from django import forms
from django.contrib.auth.models import AnonymousUser


class AddressForm(forms.ModelForm):

    class Meta:
        model = Address
        exclude = ['user', 'alias']


class UserAddressesForm(forms.Form):

    address = forms.ModelChoiceField(queryset=Address.objects.none())

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', AnonymousUser()) or AnonymousUser()
        super(UserAddressesForm, self).__init__(*args, **kwargs)

        if user.is_authenticated():
            self.fields['address'].queryset = user.addressbook
