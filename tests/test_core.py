import pytest
from mock import Mock

from saleor.core.utils import (
    Country, get_country_by_ip, get_currency_for_country)


@pytest.mark.parametrize('ip_data, expected_country', [
    ({'country': {'iso_code': 'PL'}}, Country('PL')),
    ({'country': {'iso_code': 'UNKNOWN'}}, None),
    (None, None),
    ({}, None),
    ({'country': {}}, None)])
def test_get_country_by_ip(ip_data, expected_country, monkeypatch):
    monkeypatch.setattr(
        'saleor.core.utils.georeader.get',
        Mock(return_value=ip_data))
    country = get_country_by_ip('127.0.0.1')
    assert country == expected_country


@pytest.mark.parametrize('country, expected_currency', [
    (Country('PL'), 'PLN'),
    (Country('US'), 'USD'),
    (Country('GB'), 'GBP')])
def test_get_currency_for_country(country, expected_currency, monkeypatch):
    currency = get_currency_for_country(country)
    assert currency == expected_currency
