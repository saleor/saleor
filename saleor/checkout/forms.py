"""Checkout-related forms."""
from django import forms
from django.utils.translation import pgettext_lazy


class CheckoutAddressField(forms.ChoiceField):
    """Like a choice field but uses a radio group instead of a dropdown."""

    widget = forms.RadioSelect()


class AnonymousUserShippingForm(forms.Form):
    """Additional shipping information form for users who are not logged in."""

    email = forms.EmailField(
        required=True, widget=forms.EmailInput(
            attrs={'autocomplete': 'shipping email'}),
        label=pgettext_lazy('Shipping form field label', 'Email'))
