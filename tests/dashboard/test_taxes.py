from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django_countries.fields import Country
from django_prices_vatlayer.models import VAT
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from saleor.core.utils import get_country_name_by_code
from saleor.core.utils.taxes import (
    apply_tax_to_price, get_taxes_for_address, get_taxes_for_country)
from saleor.dashboard.taxes.filters import get_country_choices_for_vat

from ..utils import compare_taxes, get_redirect_location


def test_view_taxes_list(admin_client, vatlayer):
    url = reverse('dashboard:taxes')

    response = admin_client.get(url)

    tax_list = response.context['taxes'].object_list
    assert response.status_code == 200
    assert tax_list == list(VAT.objects.order_by('country_code'))


def test_view_tax_details(admin_client, vatlayer):
    tax = VAT.objects.get(country_code='PL')
    tax_rates = [
        (rate_name, tax['value'])
        for rate_name, tax in vatlayer.items()]
    tax_rates = sorted(tax_rates)
    url = reverse('dashboard:tax-details', kwargs={'country_code': 'PL'})

    response = admin_client.get(url)
    assert response.status_code == 200
    assert response.context['tax'] == tax
    assert response.context['tax_rates'] == tax_rates


def test_configure_taxes(admin_client, site_settings):
    url = reverse('dashboard:configure-taxes')
    data = {
        'include_taxes_in_prices': False,
        'display_gross_prices': False,
        'charge_taxes_on_shipping': False}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    assert get_redirect_location(response) == reverse('dashboard:taxes')

    site_settings.refresh_from_db()
    assert not site_settings.include_taxes_in_prices
    assert not site_settings.display_gross_prices
    assert not site_settings.charge_taxes_on_shipping


@mock.patch('saleor.dashboard.taxes.views.messages', create=True)
@mock.patch('saleor.dashboard.taxes.views.call_command', create=True)
def test_fetch_tax_rates(
        mocked_call_command, mocked_messages, admin_client):
    """Ensure a valid fetch VAT rates request is correctly handled,
    and is leading to the proper VAT fetching command being invoked."""
    url = reverse('dashboard:fetch-tax-rates')
    response = admin_client.post(url)

    # Ensure the request was successful
    assert response.status_code == 302
    assert get_redirect_location(response) == reverse('dashboard:taxes')
    assert mocked_messages.success.call_count == 1

    # Ensure the get VAT rates (mocked) command was invoked
    mocked_call_command.assert_called_once_with('get_vat_rates')


@mock.patch('saleor.dashboard.taxes.views.messages', create=True)
@mock.patch('saleor.dashboard.taxes.views.logger', create=True)
@mock.patch(
    'saleor.dashboard.taxes.views.call_command',
    side_effect=ImproperlyConfigured('Test'), create=True)
def test_fetch_tax_rates_improperly_configured(
        mocked_call_command, mocked_logger, mocked_messages, admin_client):
    """Ensure a failing VAT rate fetching is leading to an error being
    returned, and that error is handled."""
    url = reverse('dashboard:fetch-tax-rates')
    response = admin_client.post(url)

    # Ensure the request was successful
    assert response.status_code == 302
    assert get_redirect_location(response) == reverse('dashboard:taxes')

    # Ensure error was logged to the logger
    # and the error was returned to the client
    assert mocked_logger.exception.call_count == 1
    assert mocked_messages.warning.call_count == 1

    # Ensure the get VAT rates (mocked) command was invoked
    mocked_call_command.assert_called_once_with('get_vat_rates')


def test_fetch_tax_rates_invalid_method(admin_client):
    """Ensure the GET method is not allowed for tax rates fetching"""
    url = reverse('dashboard:fetch-tax-rates')
    assert admin_client.get(url).status_code == 405


def test_tax_list_filters_empty(admin_client, vatlayer):
    qs = VAT.objects.order_by('country_code')
    url = reverse('dashboard:taxes')
    data = {'country_code': [''], 'sort_by': ['']}

    response = admin_client.get(url, data)

    assert response.status_code == 200
    assert list(response.context['filter_set'].qs) == list(qs)


def test_tax_list_filters_country_code(admin_client, vatlayer):
    qs = VAT.objects.filter(country_code='PL')
    url = reverse('dashboard:taxes')
    data = {'country_code': ['PL'], 'sort_by': ['']}

    response = admin_client.get(url, data)

    assert response.status_code == 200
    assert list(response.context['filter_set'].qs) == list(qs)


def test_tax_list_filters_sort_by(admin_client, vatlayer):
    qs = VAT.objects.order_by('-country_code')
    url = reverse('dashboard:taxes')
    data = {'country_code': [''], 'sort_by': ['-country_code']}

    response = admin_client.get(url, data)

    assert response.status_code == 200
    assert list(response.context['filter_set'].qs) == list(qs)


def test_get_country_choices_for_vat(vatlayer):
    expected_choices = [('DE', 'Germany'), ('PL', 'Poland')]
    choices = get_country_choices_for_vat()
    assert choices == expected_choices


def test_get_taxes_for_address(address, vatlayer):
    taxes = get_taxes_for_address(address)
    compare_taxes(taxes, vatlayer)


def test_get_taxes_for_address_fallback_default(settings, vatlayer):
    settings.DEFAULT_COUNTRY = 'PL'
    taxes = get_taxes_for_address(None)
    compare_taxes(taxes, vatlayer)


def test_get_taxes_for_address_other_country(address, vatlayer):
    address.country = 'DE'
    address.save()
    tax_rates = get_taxes_for_country(Country('DE'))

    taxes = get_taxes_for_address(address)
    compare_taxes(taxes, tax_rates)


def test_get_taxes_for_country(vatlayer):
    taxes = get_taxes_for_country(Country('PL'))
    compare_taxes(taxes, vatlayer)


def test_get_country_name_by_code():
    country_name = get_country_name_by_code('PL')
    assert country_name == 'Poland'


def test_apply_tax_to_price_do_not_include_tax(site_settings, taxes):
    site_settings.include_taxes_in_prices = False
    site_settings.save()

    money = Money(100, 'USD')
    assert apply_tax_to_price(taxes, 'standard', money) == TaxedMoney(
        net=Money(100, 'USD'), gross=Money(123, 'USD'))
    assert apply_tax_to_price(taxes, 'medical', money) == TaxedMoney(
        net=Money(100, 'USD'), gross=Money(108, 'USD'))

    taxed_money = TaxedMoney(net=Money(100, 'USD'), gross=Money(100, 'USD'))
    assert apply_tax_to_price(taxes, 'standard', taxed_money) == TaxedMoney(
        net=Money(100, 'USD'), gross=Money(123, 'USD'))
    assert apply_tax_to_price(taxes, 'medical', taxed_money) == TaxedMoney(
        net=Money(100, 'USD'), gross=Money(108, 'USD'))


def test_apply_tax_to_price_do_not_include_tax_fallback_to_standard_rate(
        site_settings, taxes):
    site_settings.include_taxes_in_prices = False
    site_settings.save()

    money = Money(100, 'USD')
    taxed_money = TaxedMoney(net=Money(100, 'USD'), gross=Money(123, 'USD'))
    assert apply_tax_to_price(taxes, 'space suits', money) == taxed_money


def test_apply_tax_to_price_include_tax(taxes):
    money = Money(100, 'USD')
    assert apply_tax_to_price(taxes, 'standard', money) == TaxedMoney(
        net=Money('81.30', 'USD'), gross=Money(100, 'USD'))
    assert apply_tax_to_price(taxes, 'medical', money) == TaxedMoney(
        net=Money('92.59', 'USD'), gross=Money(100, 'USD'))


def test_apply_tax_to_price_include_fallback_to_standard_rate(taxes):
    money = Money(100, 'USD')
    assert apply_tax_to_price(taxes, 'space suits', money) == TaxedMoney(
        net=Money('81.30', 'USD'), gross=Money(100, 'USD'))

    taxed_money = TaxedMoney(net=Money(100, 'USD'), gross=Money(100, 'USD'))
    assert apply_tax_to_price(taxes, 'space suits', taxed_money) == TaxedMoney(
        net=Money('81.30', 'USD'), gross=Money(100, 'USD'))


def test_apply_tax_to_price_raise_typeerror_for_invalid_type(taxes):
    with pytest.raises(TypeError):
        assert apply_tax_to_price(taxes, 'standard', 100)


def test_apply_tax_to_price_no_taxes_return_taxed_money():
    money = Money(100, 'USD')
    taxed_money = TaxedMoney(net=Money(100, 'USD'), gross=Money(100, 'USD'))

    assert apply_tax_to_price(None, 'standard', money) == taxed_money
    assert apply_tax_to_price(None, 'medical', taxed_money) == taxed_money


def test_apply_tax_to_price_no_taxes_return_taxed_money_range():
    money_range = MoneyRange(Money(100, 'USD'), Money(200, 'USD'))
    taxed_money_range = TaxedMoneyRange(
        TaxedMoney(net=Money(100, 'USD'), gross=Money(100, 'USD')),
        TaxedMoney(net=Money(200, 'USD'), gross=Money(200, 'USD')))

    assert (apply_tax_to_price(
        None, 'standard', money_range) == taxed_money_range)
    assert (apply_tax_to_price(
        None, 'standard', taxed_money_range) == taxed_money_range)


def test_apply_tax_to_price_no_taxes_raise_typeerror_for_invalid_type():
    with pytest.raises(TypeError):
        assert apply_tax_to_price(None, 'standard', 100)
