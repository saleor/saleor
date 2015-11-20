from collections import defaultdict

from django import forms

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
        super(AddressForm, self).__init__(*args, **kwargs)
        autocomplete_dict = defaultdict(
            lambda: 'off', self.AUTOCOMPLETE_MAPPING)
        for field_name, field in self.fields.items():
            field.widget.attrs['autocomplete'] = autocomplete_dict[field_name]
