import pytest
from mock import Mock

from saleor.core import Country, get_country_by_ip, get_currency_for_country


@pytest.mark.parametrize('reader, expected_country', [
    (Mock(return_value=Mock(get=Mock(return_value={
        'country': {'iso_code': 'PL'}}))), Country('PL')),
    (Mock(return_value=Mock(get=Mock(return_value={
        'country': {'iso_code': 'UNKNOWN'}}))), None),
    (Mock(return_value=Mock(get=Mock(return_value=None))), None),
    (Mock(return_value=Mock(get=Mock(return_value={}))), None),
    (Mock(return_value=Mock(get=Mock(return_value={'country': {}}))), None),
])
def test_get_country_by_ip(reader, expected_country, monkeypatch):
    monkeypatch.setattr('saleor.core.geolite2.reader', reader)
    country = get_country_by_ip('127.0.0.1')
    assert country == expected_country


@pytest.mark.parametrize('country, expected_currency', [
    (Country('PL'), 'PLN'),
    (Country('USA'), 'USD'),
    (Country('GB'), 'GBP')])
def test_get_currency_for_country(country, expected_currency, monkeypatch):
    currency = get_currency_for_country(country)
    assert currency == expected_currency
