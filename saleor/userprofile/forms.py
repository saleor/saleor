# encoding: utf-8
from __future__ import unicode_literals

from collections import defaultdict

from django import forms
import i18naddress

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
    I18N_MAPPING = (
        ('name', ['first_name', 'last_name']),
        ('street_address', ['street_address_1']),
        ('city_area', ['city_area']),
        ('country_area', ['country_area']),
        ('company_name', ['company_name']),
        ('postal_code', ['postal_code']),
        ('city', ['city']),
        ('sorting_code', ['sorting_code'])
    )

    class Meta:
        model = Address
        exclude = []

    def __init__(self, *args, **kwargs):
        autocomplete_type = kwargs.pop('autocomplete_type', None)
        country = kwargs.pop('country', None)
        self.country = country.code if country else None
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

    def get_country(self):
        if hasattr(self, 'cleaned_data') and self.cleaned_data.get('country'):
            return self.cleaned_data.get('country')
        return self.country

    def get_fields_order(self):
        country = self.get_country()
        if country:
            return i18naddress.get_fields_order({'country_code': country})

    def get_form_lines(self):
        fields_order = self.get_fields_order()
        field_mapping = dict(self.I18N_MAPPING)

        def _convert_to_bound_fields(form, i18n_field_names):
            bound_fields = []
            for field_name in i18n_field_names:
                local_fields = field_mapping[field_name]
                for local_name in local_fields:
                    local_field = self.fields[local_name]
                    bound_field = local_field.get_bound_field(form, local_name)
                    bound_fields.append(bound_field)
            return bound_fields

        if fields_order:
            return [_convert_to_bound_fields(self, line)
                    for line in fields_order]
