from mock import Mock
import pytest

from . import get_country_by_ip, Country


@pytest.mark.parametrize('lookup, country', [
    (Mock(return_value=Mock(country='PL')), Country('PL')),
    (Mock(return_value=Mock(country='UNKNOWN')), None),
])
def test_get_country_by_ip(lookup, country, monkeypatch):
    monkeypatch.setattr('saleor.core.geolite2.lookup', lookup)
    country = get_country_by_ip('127.0.0.1')
    assert  country == country
