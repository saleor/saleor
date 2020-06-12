import pytest
from django_countries import countries
from measurement.measures import Weight
from prices import Money

from ..models import ShippingMethod, ShippingMethodType, ShippingZone
from ..utils import default_shipping_zone_exists, get_countries_without_shipping_zone


def test_shipping_get_total(monkeypatch, shipping_zone):
    method = shipping_zone.shipping_methods.get()
    price = Money("10.0", "USD")

    assert method.get_total() == price


@pytest.mark.parametrize(
    "price, min_price, max_price, shipping_included",
    (
        (10, 10, 20, True),  # price equal min price
        (10, 1, 10, True),  # price equal max price
        (9, 10, 15, False),  # price just below min price
        (10, 1, 9, False),  # price just above max price
        (10000000, 1, None, True),  # no max price limit
        (10, 5, 15, True),
    ),
)  # regular case
def test_applicable_shipping_methods_price(
    shipping_zone, price, min_price, max_price, shipping_included
):
    method = shipping_zone.shipping_methods.create(
        minimum_order_price_amount=min_price,
        maximum_order_price_amount=max_price,
        currency="USD",
        type=ShippingMethodType.PRICE_BASED,
    )
    assert "PL" in shipping_zone.countries
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=Money(price, "USD"), weight=Weight(kg=0), country_code="PL"
    )
    assert (method in result) == shipping_included


@pytest.mark.parametrize(
    "weight, min_weight, max_weight, shipping_included",
    (
        (Weight(kg=1), Weight(kg=1), Weight(kg=2), True),  # equal min weight
        (Weight(kg=10), Weight(kg=1), Weight(kg=10), True),  # equal max weight
        (Weight(kg=5), Weight(kg=8), Weight(kg=15), False),  # below min weight
        (Weight(kg=10), Weight(kg=1), Weight(kg=9), False),  # above max weight
        (Weight(kg=10000000), Weight(kg=1), None, True),  # no max weight limit
        (Weight(kg=10), Weight(kg=5), Weight(kg=15), True),
    ),
)  # regular case
def test_applicable_shipping_methods_weight(
    weight, min_weight, max_weight, shipping_included, shipping_zone
):
    method = shipping_zone.shipping_methods.create(
        minimum_order_weight=min_weight,
        maximum_order_weight=max_weight,
        type=ShippingMethodType.WEIGHT_BASED,
    )
    assert "PL" in shipping_zone.countries
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=Money("0", "USD"), weight=weight, country_code="PL"
    )
    assert (method in result) == shipping_included


def test_applicable_shipping_methods_country_code_outside_shipping_zone(shipping_zone):
    method = shipping_zone.shipping_methods.create(
        minimum_order_price=Money("1.0", "USD"),
        maximum_order_price=Money("10.0", "USD"),
        type=ShippingMethodType.PRICE_BASED,
    )
    shipping_zone.countries = ["DE"]
    shipping_zone.save()
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=Money("5.0", "USD"), weight=Weight(kg=0), country_code="PL"
    )
    assert method not in result


def test_applicable_shipping_methods_inproper_shipping_method_type(shipping_zone):
    """Case when shipping suits the price requirements of the weight type
    shipping method and the other way around.
    """
    price_method = shipping_zone.shipping_methods.create(
        minimum_order_price=Money("1.0", "USD"),
        maximum_order_price=Money("10.0", "USD"),
        minimum_order_weight=Weight(kg=100),
        type=ShippingMethodType.WEIGHT_BASED,
    )
    weight_method = shipping_zone.shipping_methods.create(
        minimum_order_weight=Weight(kg=1),
        maximum_order_weight=Weight(kg=10),
        minimum_order_price=Money("1000.0", "USD"),
        type=ShippingMethodType.PRICE_BASED,
    )
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=Money("5.0", "USD"), weight=Weight(kg=5), country_code="PL"
    )
    assert price_method not in result
    assert weight_method not in result


def test_applicable_shipping_methods(shipping_zone):
    price_method = shipping_zone.shipping_methods.create(
        minimum_order_price=Money("1.0", "USD"),
        maximum_order_price=Money("10.0", "USD"),
        type=ShippingMethodType.PRICE_BASED,
    )
    weight_method = shipping_zone.shipping_methods.create(
        minimum_order_weight=Weight(kg=1),
        maximum_order_weight=Weight(kg=10),
        type=ShippingMethodType.WEIGHT_BASED,
    )
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=Money("5.0", "USD"), weight=Weight(kg=5), country_code="PL"
    )
    assert price_method in result
    assert weight_method in result


def test_use_default_shipping_zone(shipping_zone):
    shipping_zone.countries = ["PL"]
    shipping_zone.save()

    default_zone = ShippingZone.objects.create(default=True, name="Default")
    default_zone.countries = get_countries_without_shipping_zone()
    default_zone.save(update_fields=["countries"])

    weight_method = default_zone.shipping_methods.create(
        minimum_order_weight=Weight(kg=1),
        maximum_order_weight=Weight(kg=10),
        type=ShippingMethodType.WEIGHT_BASED,
    )
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=Money("5.0", "USD"), weight=Weight(kg=5), country_code="DE"
    )
    assert result[0] == weight_method


def test_default_shipping_zone_exists(shipping_zone):
    shipping_zone.default = True
    shipping_zone.save()
    assert default_shipping_zone_exists()
    assert not default_shipping_zone_exists(shipping_zone.pk)


def test_get_countries_without_shipping_zone(shipping_zone_without_countries):
    countries_no_shipping_zone = set(get_countries_without_shipping_zone())
    assert {c.code for c in countries} == countries_no_shipping_zone
