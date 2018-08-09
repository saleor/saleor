from django import forms
from django.utils.translation import pgettext_lazy

from ...shipping.models import ShippingZone, ShippingMethod


def currently_used_countries(shipping_zone_pk=None):
    shipping_zones = ShippingZone.objects.exclude(pk=shipping_zone_pk)
    used_countries = {
        (country.code, country.name)
        for shipping_zone in shipping_zones
        for country in shipping_zone.countries}
    return used_countries


class ShippingZoneForm(forms.ModelForm):

    class Meta:
        model = ShippingZone
        exclude = ['shipping_methods']
        labels = {
            'name': pgettext_lazy(
                'Shippment Zone field name', 'Zone Name'),
            'countries': pgettext_lazy(
                'List of countries to pick from', 'Countries')}
        help_texts = {
            'countries': pgettext_lazy(
                'Countries field help text',
                'Each country might be included in only one shipping zone.'),
            'name': pgettext_lazy(
                'Help text for ShippingZone name',
                'Name is for internal use only, it won\'t '
                'be displayed to your customers')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['countries'].choices = (
            set(self.fields['countries'].choices) - currently_used_countries(
                self.instance.pk if self.instance else None))

    def clean_countries(self):
        #TODO testme
        countries = self.cleaned_data.get('countries')
        if not countries:
            return
        duplicated_countries = set(countries).intersection(
            currently_used_countries())
        if duplicated_countries:
            self.add_error(
                'countries',
                'Countries already exists in another '
                'shipping zone: %(list_of_countries)s' % {
                    'list_of_countries': ''.join(duplicated_countries)})
        return countries


class ShippingMethodForm(forms.ModelForm):

    class Meta:
        model = ShippingMethod
        exclude = ['shipping_zone']
        labels = {
            'name': pgettext_lazy(
                'Shipping Method name', 'Name'),
            'type': pgettext_lazy(
                'Shipping Method type', 'Type'),
            'price': pgettext_lazy(
                'Currency amount', 'Price')}
