from django import forms
from django.utils.translation import pgettext_lazy

from ...checkout.forms import CheckoutAddressField


class AnonymousUserShippingForm(forms.Form):
    """Additional shipping information form for users who are not logged in."""

    email = forms.EmailField(
        required=True, widget=forms.EmailInput(
            attrs={'autocomplete': 'shipping email'}),
        label=pgettext_lazy('Shipping form field label', 'Email'))


class AddressChoiceForm(forms.Form):
    """Choose one of user's addresses or to create new one."""

    NEW_ADDRESS = 'new_address'
    CHOICES = [
        (NEW_ADDRESS, pgettext_lazy(
            'Shipping addresses form choice', 'Enter a new address'))]

    address = CheckoutAddressField(
        label=pgettext_lazy('Shipping addresses form field label', 'Address'),
        choices=CHOICES, initial=NEW_ADDRESS)

    def __init__(self, *args, **kwargs):
        addresses = kwargs.pop('addresses')
        super().__init__(*args, **kwargs)
        address_choices = [(address.id, str(address)) for address in addresses]
        self.fields['address'].choices = self.CHOICES + address_choices
