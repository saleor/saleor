from collections import defaultdict

from django import forms
from django.utils.translation import ugettext as _
from i18naddress import validate_areas

from .models import Address


class AddressForm(forms.ModelForm):

    AUTOCOMPLETE_MAPPING = (
        ('first_name', 'given-name'),
        ('last_name', 'family-name'),
        ('company_name', 'organization'),
        ('street_address_1', 'address-line1'),
        ('street_address_2', 'address-line2'),
        ('city', 'address-level2'),
        ('postal_code', 'postal-code'),
        ('country_area', 'address-level1'),
        ('country', 'country'),
        ('city_area', 'address-level3'),
        ('phone', 'tel'),
        ('email', 'email')
    )

    class Meta:
        model = Address
        exclude = []

    def __init__(self, *args, **kwargs):
        autocomplete_type = kwargs.pop('autocomplete_type', None)
        super(AddressForm, self).__init__(*args, **kwargs)
        autocomplete_dict = defaultdict(
            lambda: 'off', self.AUTOCOMPLETE_MAPPING)
        for field_name, field in self.fields.items():
            if autocomplete_type:
                autocomplete = '%s %s' % (
                    autocomplete_type, autocomplete_dict[field_name])
            else:
                autocomplete = autocomplete_dict[field_name]
            field.widget.attrs['autocomplete'] = autocomplete

    def clean(self):
        clean_data = super(AddressForm, self).clean()
        if 'country' in clean_data:
            self.validate_areas(
                clean_data['country'], clean_data.get('country_area'),
                clean_data.get('city'), clean_data.get('city_area'),
                clean_data.get('postal_code'),
                clean_data.get('street_address_1'))
        return clean_data

    def validate_areas(self, country_code, country_area,
                       city, city_area, postal_code, street_address):
        error_messages = defaultdict(
            lambda: _('Invalid value'), self.fields['country'].error_messages)
        errors, validation_data = validate_areas(
            country_code, country_area, city,
            city_area, postal_code, street_address)

        if 'country' in errors:
            self.add_error('country', _(
                '%s is not supported country code.') % country_code)
        if 'street_address' in errors:
            error = error_messages[errors['street_address']] % {
                'value': street_address}
            self.add_error('street_address_1', error)
        if 'city' in errors:
            error = error_messages[errors['city']] % {
                'value': city}
            self.add_error('city', error)
        if 'city_area' in errors:
            error = error_messages[errors['city_area']] % {
                'value': city_area}
            self.add_error('city_area', error)
        if 'country_area' in errors:
            error = error_messages[errors['country_area']] % {
                'value': country_area}
            self.add_error('country_area', error)
        if 'postal_code' in errors:
            if errors['postal_code'] == 'invalid':
                postal_code_example = validation_data[
                    'postal_code_example']
                if postal_code_example:
                    error = _(
                        'Invalid postal code. Ex. %(example)s') % {
                            'example': postal_code_example}
                else:
                    error = _('Invalid postal code.')
            else:
                error = error_messages[errors['postal_code']] % {
                    'value': postal_code}
            self.add_error('postal_code', error)
