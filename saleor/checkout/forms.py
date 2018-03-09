"""Checkout-related forms."""
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import pgettext_lazy

from ..core.utils import format_money
from ..shipping.models import ShippingMethodCountry


class CheckoutAddressField(forms.ChoiceField):
    """Like a choice field but uses a radio group instead of a dropdown."""

    widget = forms.RadioSelect()


class ShippingAddressesForm(forms.Form):
    """Shipping address form."""

    NEW_ADDRESS = 'new_address'
    CHOICES = [
        (NEW_ADDRESS, pgettext_lazy(
            'Shipping addresses form choice', 'Enter a new address'))]

    address = CheckoutAddressField(
        label=pgettext_lazy('Shipping addresses form field label', 'Address'),
        choices=CHOICES, initial=NEW_ADDRESS)

    def __init__(self, *args, **kwargs):
        additional_addresses = kwargs.pop('additional_addresses', [])
        super().__init__(*args, **kwargs)
        address_field = self.fields['address']
        address_choices = [
            (address.id, str(address)) for address in additional_addresses]
        address_field.choices = self.CHOICES + address_choices


class BillingAddressesForm(ShippingAddressesForm):
    """Billing address form."""

    NEW_ADDRESS = 'new_address'
    SHIPPING_ADDRESS = 'shipping_address'
    CHOICES = [
        (NEW_ADDRESS, pgettext_lazy(
            'Billing addresses form choice', 'Enter a new address')),
        (SHIPPING_ADDRESS, pgettext_lazy(
            'Billing addresses form choice', 'Same as shipping'))]

    address = CheckoutAddressField(choices=CHOICES, initial=SHIPPING_ADDRESS)


class BillingWithoutShippingAddressForm(ShippingAddressesForm):
    """Billing address form when shipping is not required.

    Same as the default shipping address as in this came "billing same as
    shipping" option does not make sense.
    """


# FIXME: why is this called a country choice field?
class ShippingCountryChoiceField(forms.ModelChoiceField):
    """Shipping method choice field.

    Uses a radio group instead of a dropdown and includes estimated shipping
    prices.
    """

    widget = forms.RadioSelect()

    def label_from_instance(self, obj):
        """Return a friendly label for the shipping method."""
        price_html = format_money(obj.price)
        label = mark_safe('%s %s' % (obj.shipping_method, price_html))
        return label


class ShippingMethodForm(forms.Form):
    """Shipping method form."""

    method = ShippingCountryChoiceField(
        queryset=ShippingMethodCountry.objects.select_related(
            'shipping_method').order_by('price').all(),
        label=pgettext_lazy(
            'Shipping method form field label', 'Shipping method'),
        required=True)

    def __init__(self, country_code, *args, **kwargs):
        super().__init__(*args, **kwargs)
        method_field = self.fields['method']
        if country_code:
            queryset = method_field.queryset
            method_field.queryset = queryset.unique_for_country_code(
                country_code)

        if self.initial.get('method') is None:
            self.initial['method'] = method_field.queryset.first()

        method_field.empty_label = None


class AnonymousUserShippingForm(forms.Form):
    """Additional shipping information form for users who are not logged in."""

    email = forms.EmailField(
        required=True, widget=forms.EmailInput(
            attrs={'autocomplete': 'shipping email'}),
        label=pgettext_lazy('Shipping form field label', 'Email'))


class AnonymousUserBillingForm(forms.Form):
    """Additional billing information form for users who are not logged in."""

    email = forms.EmailField(
        required=True, widget=forms.EmailInput(
            attrs={'autocomplete': 'billing email'}),
        label=pgettext_lazy('Billing form field label', 'Email'))


class NoteForm(forms.Form):
    """Form to add a note to an order."""

    note = forms.CharField(
        max_length=250, required=False, strip=True, label=False)
    note.widget = forms.Textarea({'rows': 3})

    def __init__(self, *args, **kwargs):
        self.checkout = kwargs.pop('checkout', None)
        super().__init__(*args, **kwargs)

    def set_checkout_note(self):
        self.checkout.note = self.cleaned_data.get('note', '')
