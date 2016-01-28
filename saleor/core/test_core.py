from mock import Mock
import pytest

from . import get_country_by_ip, get_currency_for_country, Country


@pytest.mark.parametrize('lookup, country', [
    (Mock(return_value=Mock(country='PL')), Country('PL')),
    (Mock(return_value=Mock(country='UNKNOWN')), None),
])
def test_get_country_by_ip(lookup, country, monkeypatch):
    monkeypatch.setattr('saleor.core.geolite2.lookup', lookup)
    country = get_country_by_ip('127.0.0.1')
    assert  country == country


@pytest.mark.parametrize('settings, country, expected_currency', [
    (Mock(AVAILABLE_CURRENCIES=['GBP', 'PLN'], DEFAULT_CURRENCY='PLN'),
     Country('PL'), 'PLN'),
    (Mock(AVAILABLE_CURRENCIES=['GBP', 'PLN'], DEFAULT_CURRENCY='PLN'),
     Country('USA'), 'PLN'),
    (Mock(AVAILABLE_CURRENCIES=['GBP', 'PLN'], DEFAULT_CURRENCY='PLN'),
     Country('GB'), 'GBP')
])
def test_get_currency_for_country(settings, country, expected_currency, monkeypatch):
    monkeypatch.setattr('saleor.core.settings', settings)
    currency = get_currency_for_country(country)
    assert  currency == expected_currency
