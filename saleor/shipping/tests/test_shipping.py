import pytest
from django_countries import countries
from measurement.measures import Weight
from prices import Money

from ..models import (
    ShippingMethod,
    ShippingMethodChannelListing,
    ShippingMethodType,
    ShippingZone,
)
from ..utils import default_shipping_zone_exists, get_countries_without_shipping_zone


@pytest.mark.parametrize(
    ("price", "min_price", "max_price", "shipping_included"),
    [
        (10, 10, 20, True),  # price equal min price
        (10, 1, 10, True),  # price equal max price
        (9, 10, 15, False),  # price just below min price
        (10, 1, 9, False),  # price just above max price
        (10000000, 1, None, True),  # no max price limit
        (10, 5, 15, True),
    ],
)  # regular case
def test_applicable_shipping_methods_price(
    shipping_zone,
    price,
    min_price,
    max_price,
    shipping_included,
    channel_USD,
    other_channel_USD,
):
    method = shipping_zone.shipping_methods.create(
        type=ShippingMethodType.PRICE_BASED,
    )
    ShippingMethodChannelListing.objects.create(
        currency=channel_USD.currency_code,
        minimum_order_price_amount=min_price,
        maximum_order_price_amount=max_price,
        shipping_method=method,
        channel=channel_USD,
    )
    ShippingMethodChannelListing.objects.create(
        currency=other_channel_USD.currency_code,
        minimum_order_price_amount=min_price,
        maximum_order_price_amount=max_price,
        shipping_method=method,
        channel=other_channel_USD,
    )
    assert "PL" in shipping_zone.countries
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=Money(price, "USD"),
        weight=Weight(kg=0),
        country_code="PL",
        channel_id=channel_USD.id,
    )
    result_ids = set([method.id for method in result])
    assert len(result_ids) == len(result)
    assert (method in result) == shipping_included


@pytest.mark.parametrize(
    ("weight", "min_weight", "max_weight", "shipping_included"),
    [
        (Weight(kg=1), Weight(kg=1), Weight(kg=2), True),  # equal min weight
        (Weight(kg=10), Weight(kg=1), Weight(kg=10), True),  # equal max weight
        (Weight(kg=5), Weight(kg=8), Weight(kg=15), False),  # below min weight
        (Weight(kg=10), Weight(kg=1), Weight(kg=9), False),  # above max weight
        (Weight(kg=10000000), Weight(kg=1), None, True),  # no max weight limit
        (Weight(kg=10), Weight(kg=5), Weight(kg=15), True),
    ],
)  # regular case
def test_applicable_shipping_methods_weight(
    weight, min_weight, max_weight, shipping_included, shipping_zone, channel_USD
):
    method = shipping_zone.shipping_methods.create(
        minimum_order_weight=min_weight,
        maximum_order_weight=max_weight,
        type=ShippingMethodType.WEIGHT_BASED,
    )
    ShippingMethodChannelListing.objects.create(
        shipping_method=method, channel=channel_USD, currency=channel_USD.currency_code
    )

    assert "PL" in shipping_zone.countries
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=Money("0", "USD"),
        weight=weight,
        country_code="PL",
        channel_id=channel_USD.id,
    )
    assert (method in result) == shipping_included


def test_applicable_shipping_methods_country_code_outside_shipping_zone(
    shipping_zone, channel_USD
):
    method = shipping_zone.shipping_methods.create(
        type=ShippingMethodType.PRICE_BASED,
    )
    ShippingMethodChannelListing.objects.create(
        minimum_order_price=Money("1.0", "USD"),
        maximum_order_price=Money("10.0", "USD"),
        shipping_method=method,
        channel=channel_USD,
    )

    shipping_zone.countries = ["DE"]
    shipping_zone.save()
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=Money("5.0", "USD"),
        weight=Weight(kg=0),
        country_code="PL",
        channel_id=channel_USD.id,
    )
    assert method not in result


def test_applicable_shipping_methods_improper_shipping_method_type(
    shipping_zone, channel_USD
):
    """Test price-based and weight-based shipping method qualification."""
    price_method = shipping_zone.shipping_methods.create(
        minimum_order_weight=Weight(kg=100),
        type=ShippingMethodType.WEIGHT_BASED,
    )
    weight_method = shipping_zone.shipping_methods.create(
        minimum_order_weight=Weight(kg=1),
        maximum_order_weight=Weight(kg=10),
        type=ShippingMethodType.PRICE_BASED,
    )
    ShippingMethodChannelListing.objects.bulk_create(
        [
            ShippingMethodChannelListing(
                minimum_order_price=Money("1.0", "USD"),
                maximum_order_price=Money("10.0", "USD"),
                shipping_method=price_method,
                channel=channel_USD,
            ),
            ShippingMethodChannelListing(
                shipping_method=weight_method,
                channel=channel_USD,
                minimum_order_price=Money("1000.0", "USD"),
            ),
        ]
    )

    result = ShippingMethod.objects.applicable_shipping_methods(
        price=Money("5.0", "USD"),
        weight=Weight(kg=5),
        country_code="PL",
        channel_id=channel_USD.id,
    )
    assert price_method not in result
    assert weight_method not in result


def test_applicable_shipping_methods(shipping_zone, channel_USD):
    price_method = shipping_zone.shipping_methods.create(
        type=ShippingMethodType.PRICE_BASED,
    )
    weight_method = shipping_zone.shipping_methods.create(
        minimum_order_weight=Weight(kg=1),
        maximum_order_weight=Weight(kg=10),
        type=ShippingMethodType.WEIGHT_BASED,
    )
    ShippingMethodChannelListing.objects.bulk_create(
        [
            ShippingMethodChannelListing(
                shipping_method=weight_method,
                channel=channel_USD,
                currency=channel_USD.currency_code,
            ),
            ShippingMethodChannelListing(
                minimum_order_price=Money("1.0", "USD"),
                maximum_order_price=Money("10.0", "USD"),
                shipping_method=price_method,
                channel=channel_USD,
                currency=channel_USD.currency_code,
            ),
        ]
    )
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=Money("5.0", "USD"),
        weight=Weight(kg=5),
        country_code="PL",
        channel_id=channel_USD.id,
    )
    assert price_method in result
    assert weight_method in result


def test_applicable_shipping_methods_with_excluded_products(
    shipping_zone, channel_USD, product, product_with_single_variant
):
    excluded_method = shipping_zone.shipping_methods.create(
        type=ShippingMethodType.PRICE_BASED,
    )
    excluded_method.excluded_products.add(product)
    weight_method = shipping_zone.shipping_methods.create(
        minimum_order_weight=Weight(kg=1),
        maximum_order_weight=Weight(kg=10),
        type=ShippingMethodType.WEIGHT_BASED,
    )
    ShippingMethodChannelListing.objects.bulk_create(
        [
            ShippingMethodChannelListing(
                shipping_method=weight_method,
                channel=channel_USD,
                currency=channel_USD.currency_code,
            ),
            ShippingMethodChannelListing(
                minimum_order_price=Money("1.0", "USD"),
                maximum_order_price=Money("10.0", "USD"),
                shipping_method=excluded_method,
                channel=channel_USD,
                currency=channel_USD.currency_code,
            ),
        ]
    )
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=Money("5.0", "USD"),
        weight=Weight(kg=5),
        country_code="PL",
        channel_id=channel_USD.id,
        product_ids=[product.id, product_with_single_variant.id],
    )
    assert excluded_method not in result
    assert weight_method in result


def test_applicable_shipping_methods_not_in_channel(shipping_zone, channel_USD):
    price_method = shipping_zone.shipping_methods.create(
        type=ShippingMethodType.PRICE_BASED,
    )
    weight_method = shipping_zone.shipping_methods.create(
        minimum_order_weight=Weight(kg=1),
        maximum_order_weight=Weight(kg=10),
        type=ShippingMethodType.WEIGHT_BASED,
    )
    ShippingMethodChannelListing.objects.create(
        shipping_method=weight_method,
        channel=channel_USD,
        currency=channel_USD.currency_code,
    )
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=Money("5.0", "USD"),
        weight=Weight(kg=5),
        country_code="PL",
        channel_id=channel_USD.id,
    )
    assert price_method not in result
    assert weight_method in result


def test_use_default_shipping_zone(shipping_zone, channel_USD):
    shipping_zone.countries = ["PL"]
    shipping_zone.save()

    default_zone = ShippingZone.objects.create(default=True, name="Default")
    default_zone.countries = get_countries_without_shipping_zone()
    default_zone.save(update_fields=["countries"])

    default_zone.channels.add(channel_USD)
    weight_method = default_zone.shipping_methods.create(
        minimum_order_weight=Weight(kg=1),
        maximum_order_weight=Weight(kg=10),
        type=ShippingMethodType.WEIGHT_BASED,
    )

    ShippingMethodChannelListing.objects.create(
        shipping_method=weight_method,
        channel=channel_USD,
        currency=channel_USD.currency_code,
    )
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=Money("5.0", "USD"),
        weight=Weight(kg=5),
        country_code="DE",
        channel_id=channel_USD.id,
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


def test_applicable_shipping_methods_price_rate_use_proper_channel(
    shipping_zone, channel_USD, other_channel_USD
):
    # given
    # Price method with different min and max in channels to total to low to apply
    price_method_1 = shipping_zone.shipping_methods.create(
        type=ShippingMethodType.PRICE_BASED,
    )
    # Price method with different min and max in channels total correct to apply
    price_method_2 = shipping_zone.shipping_methods.create(
        type=ShippingMethodType.PRICE_BASED,
    )
    # Price method with different min and max in channels total to hight to apply
    price_method_3 = shipping_zone.shipping_methods.create(
        type=ShippingMethodType.PRICE_BASED,
    )
    # Price method not assigned to channel
    price_method_4 = shipping_zone.shipping_methods.create(
        type=ShippingMethodType.PRICE_BASED,
    )

    ShippingMethodChannelListing.objects.bulk_create(
        [
            # price_method_1
            ShippingMethodChannelListing(
                minimum_order_price=Money("10.0", "USD"),
                maximum_order_price=Money("100.0", "USD"),
                shipping_method=price_method_1,
                channel=channel_USD,
            ),
            ShippingMethodChannelListing(
                minimum_order_price=Money("1.0", "USD"),
                maximum_order_price=Money("100.0", "USD"),
                shipping_method=price_method_1,
                channel=other_channel_USD,
            ),
            # price_method_2
            ShippingMethodChannelListing(
                minimum_order_price=Money("4.0", "USD"),
                maximum_order_price=Money("10.0", "USD"),
                shipping_method=price_method_2,
                channel=channel_USD,
            ),
            ShippingMethodChannelListing(
                minimum_order_price=Money("1.0", "USD"),
                maximum_order_price=Money("100.0", "USD"),
                shipping_method=price_method_2,
                channel=other_channel_USD,
            ),
            # price_method_3
            ShippingMethodChannelListing(
                minimum_order_price=Money("1.0", "USD"),
                maximum_order_price=Money("4.0", "USD"),
                shipping_method=price_method_3,
                channel=channel_USD,
            ),
            ShippingMethodChannelListing(
                minimum_order_price=Money("1.0", "USD"),
                maximum_order_price=Money("100.0", "USD"),
                shipping_method=price_method_3,
                channel=other_channel_USD,
            ),
            # price_method_4
            ShippingMethodChannelListing(
                minimum_order_price=Money("1.0", "USD"),
                maximum_order_price=Money("100.0", "USD"),
                shipping_method=price_method_4,
                channel=other_channel_USD,
            ),
        ]
    )

    # when
    result = ShippingMethod.objects.applicable_shipping_methods(
        price=Money("5.0", "USD"),
        weight=Weight(kg=5),
        country_code="PL",
        channel_id=channel_USD.id,
    )

    # then
    assert price_method_1 not in result
    assert price_method_3 not in result
    assert price_method_4 not in result
    assert price_method_2 in result
