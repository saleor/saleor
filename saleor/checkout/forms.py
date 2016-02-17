from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django_prices.templatetags.prices_i18n import format_price

from ..shipping.models import ShippingMethodCountry


class CheckoutAddressField(forms.ChoiceField):

    widget = forms.RadioSelect()


class ShippingAddressesForm(forms.Form):

    NEW_ADDRESS = 'new_address'
    CHOICES = (
        (NEW_ADDRESS, _('Enter a new address')),
    )

    address = CheckoutAddressField(choices=CHOICES, initial=NEW_ADDRESS)

    def __init__(self, *args, **kwargs):
        additional_addresses = kwargs.pop('additional_addresses', [])
        super(ShippingAddressesForm, self).__init__(*args, **kwargs)
        address_field = self.fields['address']
        address_choices = [
            (address.id, str(address)) for address in additional_addresses]
        address_field.choices = list(self.CHOICES) + address_choices


class BillingAddressesForm(ShippingAddressesForm):

    NEW_ADDRESS = 'new_address'
    SHIPPING_ADDRESS = 'shipping_address'
    CHOICES = (
        (NEW_ADDRESS, _('Enter a new address')),
        (SHIPPING_ADDRESS, _('Same as shipping'))
    )

    address = CheckoutAddressField(choices=CHOICES, initial=SHIPPING_ADDRESS)


class BillingWithoutShippingAddressForm(ShippingAddressesForm):

    pass


class ShippingCountryChoiceField(forms.ModelChoiceField):

    widget = forms.RadioSelect()

    def label_from_instance(self, obj):
        price_html = format_price(obj.price.gross, obj.price.currency)
        label = mark_safe('%s %s' % (obj.shipping_method, price_html))
        return label


class ShippingMethodForm(forms.Form):

    method = ShippingCountryChoiceField(
        queryset=ShippingMethodCountry.objects.select_related(
            'shipping_method').order_by('price').all(),
        label=_('Shipping method'), required=True)

    def __init__(self, country_code, *args, **kwargs):
        super(ShippingMethodForm, self).__init__(*args, **kwargs)
        method_field = self.fields['method']
        if country_code:
            queryset = method_field.queryset
            method_field.queryset = queryset.unique_for_country_code(country_code)
        if self.initial.get('method') is None:
            method_field.initial = method_field.queryset.first()
        method_field.empty_label = None


class AnonymousUserShippingForm(forms.Form):

    email = forms.EmailField(
        required=True, widget=forms.EmailInput(attrs={'autocomplete': 'shipping email'}))


class AnonymousUserBillingForm(forms.Form):

    email = forms.EmailField(
        required=True, widget=forms.EmailInput(attrs={'autocomplete': 'billing email'}))
