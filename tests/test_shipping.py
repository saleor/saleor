from unittest.mock import Mock

import pytest

from prices import Money, TaxedMoney
from saleor.core.i18n import ANY_COUNTRY, COUNTRY_CODE_CHOICES
from saleor.core.utils import format_money, get_country_name_by_code
from saleor.shipping.models import ShippingRate
from saleor.shipping.utils import country_choices, get_taxed_shipping_price


@pytest.mark.parametrize('price, charge_taxes, expected_price', [
    (Money(10, 'USD'), False, TaxedMoney(
        net=Money(10, 'USD'), gross=Money(10, 'USD'))),
    (Money(10, 'USD'), True, TaxedMoney(
        net=Money('8.13', 'USD'), gross=Money(10, 'USD')))])
def test_get_taxed_shipping_price(
        site_settings, vatlayer, price, charge_taxes, expected_price):
    site_settings.charge_taxes_on_shipping = charge_taxes
    site_settings.save()

    shipping_price = get_taxed_shipping_price(price, taxes=vatlayer)

    assert shipping_price == expected_price


def test_shipping_get_total_price(monkeypatch, shipping_method, vatlayer):
    method = shipping_method.shipping_methods.get()
    price = Money(10, 'USD')
    taxed_price = TaxedMoney(
        net=Money('8.13', 'USD'), gross=Money(10, 'USD'))
    mock_get_price = Mock(return_value=taxed_price)
    monkeypatch.setattr(
        'saleor.shipping.models.get_taxed_shipping_price', mock_get_price)
    method.get_total_price(taxes=vatlayer)
    mock_get_price.assert_called_once_with(price, vatlayer)


def test_shipping_get_ajax_label(shipping_method):
    method = shipping_method.shipping_methods.get()
    label = method.get_ajax_label()
    proper_label = '%(shipping_method)s %(country_code_display)s %(price)s' % {
        'shipping_method': method.shipping_method,
        'country_code_display': method.get_country_code_display(),
        'price': format_money(method.price)}
    assert label == proper_label


def test_country_choices(shipping_method):
    any_country_shipping_method = ShippingRate.objects.filter(
        country_code=ANY_COUNTRY)
    assert any_country_shipping_method.exists()
    assert country_choices() == COUNTRY_CODE_CHOICES

    any_country_shipping_method.delete()
    ShippingRate.objects.create(
        country_code='PL', price=10, shipping_method=shipping_method)
    assert country_choices() == [('PL', get_country_name_by_code('PL'))]
