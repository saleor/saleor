from django import forms
from django.utils.translation import ugettext as _

from .models import Address, AddressBook


class AddressForm(forms.ModelForm):

    class Meta:
        model = Address


class AddressBookForm(forms.ModelForm):

    class Meta:
        model = AddressBook
        fields = ['alias']

    def clean(self):
        super(AddressBookForm, self).clean()
        if AddressBook.objects.filter(
            user_id=self.instance.user_id, alias=self.cleaned_data.get('alias')
        ).exclude(address=self.instance.address_id).exists():
            self._errors['alias'] = self.error_class(
                [_('You are already using such alias for another address')])

        return self.cleaned_data
