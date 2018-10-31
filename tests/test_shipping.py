from unittest.mock import Mock

import pytest
from measurement.measures import Weight
from prices import Money, TaxedMoney

from saleor.core.utils import format_money
from saleor.core.utils.taxes import get_taxed_shipping_price
from saleor.shipping.models import (
    ShippingMethod, ShippingMethodType, ShippingZone)
from .utils import money

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


def test_shipping_get_total(monkeypatch, shipping_zone, vatlayer):
    method = shipping_zone.shipping_methods.get()
    price = Money(10, 'USD')
    taxed_price = TaxedMoney(
        net=Money('8.13', 'USD'), gross=Money(10, 'USD'))
    mock_get_price = Mock(return_value=taxed_price)
    monkeypatch.setattr(
        'saleor.shipping.models.get_taxed_shipping_price', mock_get_price)
    method.get_total(taxes=vatlayer)
    mock_get_price.assert_called_once_with(price, vatlayer)


def test_shipping_get_ajax_label(shipping_zone):
    shipping_method = shipping_zone.shipping_methods.get()
    label = shipping_method.get_ajax_label()
    proper_label = '%(shipping_method)s %(price)s' % {
        'shipping_method': shipping_method,
        'price': format_money(shipping_method.price)}
    assert label == proper_label


@pytest.mark.parametrize(
    'price, min_price, max_price, shipping_included', (
        (money(10), money(10), money(20), True),  # price equal min price
        (money(10), money(1), money(10), True),  # price equal max price
        (money(9), money(10), money(15), False),  # price just below min price
        (money(10), money(1), money(9), False),  # price just above max price
        (money(10000000), money(1), None, True),  # no max price limit
        (money(10), money(5), money(15), True)))  # regular case
def test_applicable_shipping_methods_price(
        shipping_zone, price, min_price, max_price, shipping_included):
    method = shipping_zone.shipping_methods.create(
        minimum_order_price=min_price, maximum_order_price=max_price,
        type=ShippingMethodType.PRICE_BASED)
    assert 'PL' in shipping_zone.countries
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=price, weight=Weight(kg=0), country_code='PL')
    assert (method in result) == shipping_included


@pytest.mark.parametrize(
    'weight, min_weight, max_weight, shipping_included', (
        (Weight(kg=1), Weight(kg=1), Weight(kg=2), True),  # equal min weight
        (Weight(kg=10), Weight(kg=1), Weight(kg=10), True),  # equal max weight
        (Weight(kg=5), Weight(kg=8), Weight(kg=15), False),  # below min weight
        (Weight(kg=10), Weight(kg=1), Weight(kg=9), False),  # above max weight
        (Weight(kg=10000000), Weight(kg=1), None, True),  # no max weight limit
        (Weight(kg=10), Weight(kg=5), Weight(kg=15), True)))  # regular case
def test_applicable_shipping_methods_weight(
        weight, min_weight, max_weight, shipping_included, shipping_zone):
    method = shipping_zone.shipping_methods.create(
        minimum_order_weight=min_weight, maximum_order_weight=max_weight,
        type=ShippingMethodType.WEIGHT_BASED)
    assert 'PL' in shipping_zone.countries
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=money(0), weight=weight, country_code='PL')
    assert (method in result) == shipping_included


def test_applicable_shipping_methods_country_code_outside_shipping_zone(
        shipping_zone):
    method = shipping_zone.shipping_methods.create(
        minimum_order_price=money(1), maximum_order_price=money(10),
        type=ShippingMethodType.PRICE_BASED)
    shipping_zone.countries = ['DE']
    shipping_zone.save()
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=money(5), weight=Weight(kg=0), country_code='PL')
    assert method not in result


def test_applicable_shipping_methods_inproper_shipping_method_type(
        shipping_zone):
    """Case when shipping suits the price requirements of the weight type
    shipping method and the other way around.
    """
    price_method = shipping_zone.shipping_methods.create(
        minimum_order_price=money(1), maximum_order_price=money(10),
        minimum_order_weight=Weight(kg=100),
        type=ShippingMethodType.WEIGHT_BASED)
    weight_method = shipping_zone.shipping_methods.create(
        minimum_order_weight=Weight(kg=1), maximum_order_weight=Weight(kg=10),
        minimum_order_price=money(1000), type=ShippingMethodType.PRICE_BASED)
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=money(5), weight=Weight(kg=5), country_code='PL')
    assert price_method not in result
    assert weight_method not in result


def test_applicable_shipping_methods(shipping_zone):
    price_method = shipping_zone.shipping_methods.create(
        minimum_order_price=money(1), maximum_order_price=money(10),
        type=ShippingMethodType.PRICE_BASED)
    weight_method = shipping_zone.shipping_methods.create(
        minimum_order_weight=Weight(kg=1), maximum_order_weight=Weight(kg=10),
        type=ShippingMethodType.WEIGHT_BASED)
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=money(5), weight=Weight(kg=5), country_code='PL')
    assert price_method in result
    assert weight_method in result


def test_use_default_shipping_zone(shipping_zone):
    shipping_zone.countries = ['PL']
    shipping_zone.save()

    default_zone = ShippingZone.objects.create(default=True, name='Default')
    weight_method = default_zone.shipping_methods.create(
        minimum_order_weight=Weight(kg=1), maximum_order_weight=Weight(kg=10),
        type=ShippingMethodType.WEIGHT_BASED)
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=money(5), weight=Weight(kg=5), country_code='DE')
    assert result[0] == weight_method


@pytest.mark.parametrize(
    'countries, result',
    (
        (['PL'], 'Poland'),
        (['PL', 'DE', 'IT'], 'Poland, Germany, Italy'),
        (['PL', 'DE', 'IT', 'LE'], '4 countries'),
        ([], '0 countries')))
def test_countries_display(shipping_zone, countries, result):
    shipping_zone.countries = countries
    shipping_zone.save()
    assert shipping_zone.countries_display() == result
