import os
import re
import uuid
from unittest.mock import patch
from urllib.parse import urlencode

import i18naddress
import pytest
from captcha import constants as recaptcha_constants
from captcha.client import RecaptchaResponse
from django.core.exceptions import ValidationError
from django.core.files import File
from django.forms import Form
from django.http import QueryDict
from django.template import Context, Template
from django.urls import reverse
from django_countries.fields import Country

from saleor.account import forms, i18n
from saleor.account.forms import FormWithReCaptcha, NameForm
from saleor.account.models import User
from saleor.account.templatetags.i18n_address_tags import format_address
from saleor.account.utils import (
    get_random_avatar, get_user_first_name, get_user_last_name)
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


def test_order_with_lines_pagination(authorized_client, order_list, settings):
    settings.PAGINATE_BY = 1
    data = {'page': '1'}
    url = reverse('account:details')
    response = authorized_client.get(url, data)
    assert response.status_code == 200

    data = {'page': '2'}
    url = reverse('account:details')
    response = authorized_client.get(url, data)
    assert response.status_code == 200


def test_format_address(address):
    formatted_address = format_address(address)
    address_html = '<br>'.join(map(str, formatted_address['address_lines']))
    context = Context({'address': address})
    tpl = Template(
        '{% load i18n_address_tags %}'
        '{% format_address address %}')
    rendered_html = tpl.render(context)
    assert address_html in rendered_html
    assert 'inline-address' not in rendered_html
    assert str(address.phone) in rendered_html


def test_format_address_all_options(address):
    formatted_address = format_address(
        address, include_phone=False, inline=True, latin=True)
    address_html = ', '.join(map(str, formatted_address['address_lines']))
    context = Context({'address': address})
    tpl = Template(
        r'{% load i18n_address_tags %}'
        r'{% format_address address include_phone=False inline=True'
        r' latin=True %}')
    rendered_html = tpl.render(context)
    assert address_html in rendered_html
    assert 'inline-address' in rendered_html
    assert str(address.phone) not in rendered_html


def test_address_as_data(address):
    data = address.as_data()
    assert data == {
        'first_name': 'John',
        'last_name': 'Doe',
        'company_name': 'Mirumee Software',
        'street_address_1': 'Tęczowa 7',
        'street_address_2': '',
        'city': 'WROCŁAW',
        'city_area': '',
        'postal_code': '53-601',
        'country': 'PL',
        'country_area': '',
        'phone': '+48713988102'}


def test_copy_address(address):
    copied_address = address.get_copy()
    assert copied_address.pk != address.pk
    assert copied_address == address


def test_compare_addresses(address):
    copied_address = address.get_copy()
    assert address == copied_address


def test_compare_addresses_with_country_object(address):
    copied_address = address.get_copy()
    copied_address.country = Country('PL')
    copied_address.save()
    assert address == copied_address


def test_compare_addresses_different_country(address):
    copied_address = address.get_copy()
    copied_address.country = Country('FR')
    copied_address.save()
    assert address != copied_address


def test_user_ajax_label(customer_user):
    address = customer_user.default_billing_address
    label = '%s %s (%s)' % (
        address.first_name, address.last_name, customer_user.email)
    assert customer_user.get_ajax_label() == label


def test_user_ajax_label_without_address(admin_user):
    assert admin_user.get_ajax_label() == admin_user.email


@pytest.mark.parametrize("email, first_name, last_name, full_name", [
    ('John@example.com', 'John', 'Doe', 'John Doe'),
    ('John@example.com', 'John', '', 'John'),
    ('John@example.com', '', 'Doe', 'Doe'),
    ('John@example.com', '', '', 'John@example.com'),
])
def test_get_full_name_user_with_names(email, first_name,
                                       last_name, full_name, address):
    user = User(email=email, first_name=first_name, last_name=last_name)
    assert user.get_full_name() == full_name


@pytest.mark.parametrize("email, first_name, last_name, full_name", [
    ('John@example.com', 'John', 'Doe', 'John Doe'),
    ('John@example.com', 'John', '', 'John'),
    ('John@example.com', '', 'Doe', 'Doe'),
    ('John@example.com', '', '', 'John@example.com'),
])
def test_get_full_name_user_with_address(email, first_name,
                                         last_name, full_name, address):
    address.first_name = first_name
    address.last_name = last_name
    user = User(email=email, default_billing_address=address)
    assert user.get_full_name() == full_name


@pytest.mark.parametrize("email, first_name, last_name, full_name", [
    ('John@example.com', 'John', 'Doe', 'John Doe'),
    ('John@example.com', 'John', '', 'John'),
    ('John@example.com', '', 'Doe', 'Doe'),
    ('John@example.com', '', '', 'Arnold Green'),
])
def test_get_full_name(email, first_name, last_name, full_name, address):
    address.first_name = "Arnold"
    address.last_name = "Green"
    user = User(
        email=email, first_name=first_name, last_name=last_name,
        default_billing_address=address)
    assert user.get_full_name() == full_name


@pytest.mark.parametrize(
    "first_name, default_billing_address_first_name, result", [
        ('John', 'Arnold', 'John'),
        ('John', '', 'John'),
        ('', 'Arnold', 'Arnold'),
        ('', '', '')])
def test_get_user_first_name(first_name, default_billing_address_first_name,
                             result, address):
    address.first_name = default_billing_address_first_name
    user = User(first_name=first_name, default_billing_address=address)
    assert get_user_first_name(user) == result


@pytest.mark.parametrize(
    "last_name, default_billing_address_last_name, result", [
        ('Doe', 'Green', 'Doe'),
        ('Doe', '', 'Doe'),
        ('', 'Green', 'Green'),
        ('', '', '')])
def test_get_user_last_name(last_name, default_billing_address_last_name,
                            result, address):
    address.last_name = default_billing_address_last_name
    user = User(last_name=last_name, default_billing_address=address)
    assert get_user_last_name(user) == result


def test_get_random_avatar():
    avatar = get_random_avatar()
    assert isinstance(avatar, File)
    assert re.match(r"avatar\d+.png", avatar.name)


def test_disabled_recaptcha():
    """
    This test creates a new form that should not contain any recaptcha field.
    """
    class TestForm(Form, FormWithReCaptcha):
        pass

    form = TestForm({})
    assert form.is_valid()


@patch('captcha.fields.client.submit')
def test_requires_recaptcha(captcha_submit_mock, settings):
    """
    This test creates a new form
    that should contain a (required) recaptcha field.
    """
    captcha_submit_mock.return_value = RecaptchaResponse(is_valid=True)

    settings.RECAPTCHA_PUBLIC_KEY = recaptcha_constants.TEST_PUBLIC_KEY
    settings.RECAPTCHA_PRIVATE_KEY = recaptcha_constants.TEST_PRIVATE_KEY

    class TestForm(Form, FormWithReCaptcha):
        pass

    form = TestForm({})
    assert not form.is_valid()

    form = TestForm({'g-recaptcha-response': 'PASSED'})
    assert form.is_valid()


def test_view_account_delete_login_required(customer_user, client):
    url = reverse('account:delete')
    response = client.post(url)
    assert response.status_code == 302


def test_view_account_post_required(customer_user, authorized_client):
    url = reverse('account:delete')
    response = authorized_client.get(url)
    assert response.status_code == 405


@patch('saleor.account.views.send_account_delete_confirmation_email.delay')
def test_view_account_delete(
        send_confirmation_mock, customer_user, authorized_client, staff_user):
    url = reverse('account:delete')
    response = authorized_client.post(url)
    assert response.status_code == 302
    send_confirmation_mock.assert_called_once_with(
        str(customer_user.token), customer_user.email)


def test_view_account_delete_confirm(customer_user, authorized_client):
    # Non existing token
    url = reverse('account:delete-confirm', args=[str(uuid.uuid4())])
    response = authorized_client.get(url)
    assert response.status_code == 404

    deletion_url = reverse(
        'account:delete-confirm', args=[customer_user.token])

    # getting the page should not delete the user
    response = authorized_client.get(deletion_url)
    assert response.status_code == 200
    customer_user = User.objects.filter(pk=customer_user.pk).first()
    assert customer_user is not None

    # posting onto the page should delete the user
    response = authorized_client.post(deletion_url)
    assert response.status_code == 302
    customer_user = User.objects.filter(pk=customer_user.pk).first()
    assert customer_user is None


def test_form_add_names_to_user(customer_user):
    name_form = NameForm(
        {'first_name': 'Jan', 'last_name': 'Nowak'},
        instance=customer_user)
    name_form.is_valid()
    name_form.save()
    updated_user = User.objects.get(pk=customer_user.pk)
    assert updated_user.first_name == 'Jan'
    assert updated_user.last_name == 'Nowak'


def test_view_add_names_to_user(customer_user, authorized_client):
    url = reverse('account:details')
    response = authorized_client.post(
        url, data={'first_name': 'Jan', 'last_name': 'Nowak'})
    assert response.status_code == 200
    updated_user = User.objects.get(pk=customer_user.pk)
    assert updated_user.first_name == 'Jan'
    assert updated_user.last_name == 'Nowak'
