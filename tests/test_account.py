from urllib.parse import urlencode

import i18naddress
import pytest
from django.core.exceptions import ValidationError
from django.http import QueryDict
from django.template import Context, Template
from django.urls import reverse
from django_countries.fields import Country

from saleor.account import forms, i18n
from saleor.account.templatetags.i18n_address_tags import format_address
from saleor.account.validators import validate_possible_number


@pytest.mark.parametrize('country', ['CN', 'PL', 'US'])
def test_address_form_for_country(country):
    data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'country': country,
        'phone': '123456789'}

    form = forms.get_address_form(data, country_code=country)[0]
    errors = form.errors
    rules = i18naddress.get_validation_rules({'country_code': country})
    required = rules.required_fields
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


def test_address_form_postal_code_validation():
    data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'country': 'PL',
        'postal_code': 'XXX'}
    form = forms.get_address_form(data, country_code='PL')[0]
    errors = form.errors
    assert 'postal_code' in errors


@pytest.mark.parametrize(
    'form_data, form_valid, expected_preview, expected_country', [
        ({'preview': True}, False, True, 'PL'),
        ({
            'preview': False,
            'street_address_1': 'Foo bar',
            'postal_code': '00-123',
            'city': 'Warsaw'}, True, False, 'PL'),
        ({'preview': True, 'country': 'US'}, False, True, 'US'),
        ({
            'preview': False,
            'street_address_1': 'Foo bar',
            'postal_code': '0213',
            'city': 'Warsaw'}, False, False, 'PL')])
def test_get_address_form(
        form_data, form_valid, expected_preview, expected_country):
    data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'country': 'PL'}
    data.update(form_data)
    query_dict = urlencode(data)
    form, preview = forms.get_address_form(
        data=QueryDict(query_dict), country_code=data['country'])
    assert preview is expected_preview
    assert form.is_valid() is form_valid
    assert form.i18n_country_code == expected_country


def test_country_aware_form_has_only_supported_countries():
    default_form = i18n.COUNTRY_FORMS['US']
    instance = default_form()
    country_field = instance.fields['country']
    country_choices = [code for code, label in country_field.choices]

    for country in i18n.UNKNOWN_COUNTRIES:
        assert country not in i18n.COUNTRY_FORMS
        assert country not in country_choices


@pytest.mark.parametrize("input,exception", [
    ('123', ValidationError),
    ('+48123456789', None),
    ('+12025550169', None),
    ('+481234567890', ValidationError),
    ('testext', ValidationError),
])
def test_validate_possible_number(input, exception):
    if exception is not None:
        with pytest.raises(exception):
            validate_possible_number(input)
    else:
        validate_possible_number(input)


def test_order_with_lines_pagination(admin_client, order_list, settings):
    settings.PAGINATE_BY = 1
    data = {'page': '1'}
    url = reverse('account:details')
    response = admin_client.get(url, data)
    assert response.status_code == 200

    data = {'page': '2'}
    url = reverse('account:details')
    response = admin_client.get(url, data)
    assert response.status_code == 200


def test_format_address(billing_address):
    formatted_address = format_address(billing_address)
    address_html = '<br>'.join(map(str, formatted_address['address_lines']))
    context = Context({'address': billing_address})
    tpl = Template(
        '{% load i18n_address_tags %}'
        '{% format_address address %}')
    rendered_html = tpl.render(context)
    assert address_html in rendered_html
    assert 'inline-address' not in rendered_html
    assert str(billing_address.phone) in rendered_html


def test_format_address_all_options(billing_address):
    formatted_address = format_address(
        billing_address, include_phone=False, inline=True, latin=True)
    address_html = ', '.join(map(str, formatted_address['address_lines']))
    context = Context({'address': billing_address})
    tpl = Template(
        r'{% load i18n_address_tags %}'
        r'{% format_address address include_phone=False inline=True'
        r' latin=True %}')
    rendered_html = tpl.render(context)
    assert address_html in rendered_html
    assert 'inline-address' in rendered_html
    assert str(billing_address.phone) not in rendered_html


def test_address_as_data(billing_address):
    data = billing_address.as_data()
    assert data == {
        'first_name': 'John',
        'last_name': 'Doe',
        'company_name': 'Mirumee Software',
        'street_address_1': 'Tęczowa 7',
        'street_address_2': '',
        'city': 'Wrocław',
        'city_area': '',
        'postal_code': '53-601',
        'country': 'PL',
        'country_area': '',
        'phone': '+48713988102'}


def test_copy_address(billing_address):
    copied_address = billing_address.get_copy()
    assert copied_address.pk != billing_address.pk
    assert copied_address == billing_address


def test_compare_addresses(billing_address):
    copied_address = billing_address.get_copy()
    assert billing_address == copied_address


def test_compare_addresses_with_country_object(billing_address):
    copied_address = billing_address.get_copy()
    copied_address.country = Country('PL')
    copied_address.save()
    assert billing_address == copied_address


def test_compare_addresses_different_country(billing_address):
    copied_address = billing_address.get_copy()
    copied_address.country = Country('FR')
    copied_address.save()
    assert billing_address != copied_address
