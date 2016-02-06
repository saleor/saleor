import i18naddress
import pytest

from . import forms


@pytest.mark.parametrize('country', ['CN', 'PL', 'US'])
def test_address_form_for_country(country):
    data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'country': country}
    form = forms.AddressForm(data)
    errors = form.errors
    required = i18naddress.validate_areas(country)[0]
    if 'street_address' in required:
        assert 'street_address_1' in errors
    else:
        assert 'street_address_1' not in errors
    if 'city' in required:
        assert 'city' in errors
    else:
        assert 'city' not in errors
    if 'city_area' in required:
        assert 'city_area' in errors
    else:
        assert 'city_area' not in errors
    if 'country_area' in required:
        assert 'country_area' in errors
    else:
        assert 'country_area' not in errors
    if 'postal_code' in required:
        assert 'postal_code' in errors
    else:
        assert 'postal_code' not in errors
