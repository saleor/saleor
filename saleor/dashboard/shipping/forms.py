from django import forms
from django.utils.translation import pgettext_lazy

from ...account.i18n import COUNTRY_CHOICES
from ...core.weight import WeightField
from ...shipping import ShippingMethodType
from ...shipping.models import ShippingMethod, ShippingZone
from ...site.models import SiteSettings


def currently_used_countries(zone_pk=None):
    shipping_zones = ShippingZone.objects.exclude(pk=zone_pk)
    used_countries = {
        (country.code, country.name)
        for shipping_zone in shipping_zones
        for country in shipping_zone.countries}
    return used_countries


def get_available_countries(zone_pk=None):
    return set(COUNTRY_CHOICES) - currently_used_countries(zone_pk)


def default_shipping_zone_exists(zone_pk=None):
    return ShippingZone.objects.exclude(pk=zone_pk).filter(default=True)


class ChangeDefaultWeightUnit(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ['default_weight_unit']
        labels = {
            'default_weight_unit': pgettext_lazy(
                'Label of the default weight unit picker',
                'Default weight unit')}
        help_texts = {
            'default_weight_unit': pgettext_lazy(
                'Default weight unit help text',
                'Default unit for weights entered from the dashboard.'
                'All weights will be recalculated to the new unit.')}


class ShippingZoneForm(forms.ModelForm):
    class Meta:
        model = ShippingZone
        fields = ['name', 'default', 'countries']
        labels = {
            'name': pgettext_lazy(
                'Shippment Zone field name', 'Shipping zone name'),
            'default': pgettext_lazy(
                'Shipping Zone field name', 'Rest of World'),
            'countries': pgettext_lazy(
                'List of countries to pick from', 'Countries')}
        help_texts = {
            'countries': pgettext_lazy(
                'Countries field help text',
                'Each country might be included in only one shipping zone.'),
            'name': pgettext_lazy(
                'Help text for ShippingZone name',
                'Name is for internal use only, it won\'t '
                'be displayed to your customers'),
            'default': pgettext_lazy(
                'Help text for ShippingZone name',
                'If selected, this zone will include any countries that'
                ' are not already listed in your other shipping zones.')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pk = self.instance.pk if self.instance else None
        available_countries = get_available_countries(pk)
        self.fields['countries'].choices = sorted(
            available_countries, key=lambda choice: choice[1])

        if default_shipping_zone_exists(pk):
            self.fields['default'].disabled = True
            self.fields['countries'].required = True

    def clean_default(self):
        default = self.cleaned_data.get('default')
        if not default:
            return default
        shipping_zone_exists = default_shipping_zone_exists(
            self.instance.pk if self.instance else None)
        if not shipping_zone_exists:
            return default
        self.add_error(
            'default', pgettext_lazy(
                'ShippingZone  with "default" option selected already exists',
                'Default ShippingZone already exists.'))
        return default

    def clean_countries(self):
        countries = self.cleaned_data.get('countries')
        if not countries:
            return
        duplicated_countries = set(countries).intersection(
            currently_used_countries())
        if duplicated_countries:
            self.add_error(
                'countries', pgettext_lazy(
                    'Shipping zone containing duplicated countries form error',
                    'Countries already exists in another '
                    'shipping zone: %(list_of_countries)s' % {
                        'list_of_countries': ', '.join(duplicated_countries)}))
        return countries

    def clean(self):
        data = super().clean()
        if not data.get('default') and not data.get('countries'):
            self.add_error('countries', pgettext_lazy(
                'ShippingZone field error', 'This field is required.'))
        if data.get('default'):
            data['countries'] = []
        return data


class ShippingMethodForm(forms.ModelForm):
    class Meta:
        model = ShippingMethod
        fields = ['name', 'price']
        labels = {
            'name': pgettext_lazy('Shipping Method name', 'Name'),
            'price': pgettext_lazy('Currency amount', 'Price')}
        help_texts = {
            'name': pgettext_lazy(
                'Shipping method name help text',
                'Customers will see this at the checkout.')}


class PriceShippingMethodForm(forms.ModelForm):
    class Meta(ShippingMethodForm.Meta):
        labels = {
            'minimum_order_price': pgettext_lazy(
                'Minimum order price to use this shipping method',
                'Minimum order price'),
            'maximum_order_price': pgettext_lazy(
                'Maximum order price to use this order',
                'Maximum order price')}
        labels.update(ShippingMethodForm.Meta.labels)
        fields = [
            'name', 'price', 'minimum_order_price', 'maximum_order_price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['maximum_order_price'].widget.attrs['placeholder'] = (
            pgettext_lazy(
                'Placeholder for maximum order price set to unlimited',
                'No limit'))
        self.fields['minimum_order_price'].widget.attrs['placeholder'] = '0'

    def clean_minimum_order_price(self):
        return self.cleaned_data['minimum_order_price'] or 0

    def clean(self):
        data = super().clean()
        min_price = data.get('minimum_order_price')
        max_price = data.get('maximum_order_price')
        if min_price and max_price is not None and max_price <= min_price:
            self.add_error('maximum_order_price', pgettext_lazy(
                'Price shipping method form error',
                'Maximum order price should be larger'
                ' than the minimum order price.'))
        return data


class WeightShippingMethodForm(forms.ModelForm):
    minimum_order_weight = WeightField(
        required=False, label=pgettext_lazy(
            'Minimum order weight to use this shipping method',
            'Minimum order weight'))
    maximum_order_weight = WeightField(
        required=False, label=pgettext_lazy(
            'Maximum order weight to use this shipping method',
            'Maximum order weight'))

    class Meta(ShippingMethodForm.Meta):
        fields = [
            'name', 'price', 'minimum_order_weight', 'maximum_order_weight']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['maximum_order_weight'].widget.attrs['placeholder'] = (
            pgettext_lazy(
                'Placeholder for maximum order weight set to unlimited',
                'No limit'))
        self.fields['minimum_order_weight'].widget.attrs['placeholder'] = '0'

    def clean_minimum_order_weight(self):
        return self.cleaned_data['minimum_order_weight'] or 0

    def clean(self):
        data = super().clean()
        min_weight = data.get('minimum_order_weight')
        max_weight = data.get('maximum_order_weight')
        if min_weight and max_weight is not None and max_weight <= min_weight:
            self.add_error('maximum_order_weight', pgettext_lazy(
                'Price shipping method form error',
                'Maximum order price should be larger'
                ' than the minimum order price.'))
        return data


def get_shipping_form(type):
    if type == ShippingMethodType.WEIGHT_BASED:
        return WeightShippingMethodForm
    elif type == ShippingMethodType.PRICE_BASED:
        return PriceShippingMethodForm
    raise TypeError('Unknown form type: %s' % type)
