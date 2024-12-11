import pytest

from ....core.prices import Money
from ...models import ShippingMethod, ShippingMethodChannelListing, ShippingMethodType


@pytest.fixture
def shipping_method(shipping_zone, channel_USD, default_tax_class):
    method = ShippingMethod.objects.create(
        name="DHL",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
        maximum_delivery_days=10,
        minimum_delivery_days=5,
        tax_class=default_tax_class,
    )
    ShippingMethodChannelListing.objects.create(
        shipping_method=method,
        channel=channel_USD,
        minimum_order_price=Money(0, "USD"),
        price=Money(10, "USD"),
    )
    return method


@pytest.fixture
def other_shipping_method(shipping_zone, channel_USD):
    method = ShippingMethod.objects.create(
        name="DPD",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
    )
    ShippingMethodChannelListing.objects.create(
        channel=channel_USD,
        shipping_method=method,
        minimum_order_price=Money(0, "USD"),
        price=Money(9, "USD"),
    )
    return method


@pytest.fixture
def shipping_method_weight_based(shipping_zone, channel_USD):
    method = ShippingMethod.objects.create(
        name="weight based method",
        type=ShippingMethodType.WEIGHT_BASED,
        shipping_zone=shipping_zone,
        maximum_delivery_days=10,
        minimum_delivery_days=5,
    )
    ShippingMethodChannelListing.objects.create(
        shipping_method=method,
        channel=channel_USD,
        minimum_order_price=Money(0, "USD"),
        price=Money(10, "USD"),
    )
    return method


@pytest.fixture
def shipping_method_excluded_by_postal_code(shipping_method):
    shipping_method.postal_code_rules.create(start="HB2", end="HB6")
    return shipping_method


@pytest.fixture
def shipping_method_channel_PLN(shipping_zone, channel_PLN):
    shipping_zone.channels.add(channel_PLN)
    method = ShippingMethod.objects.create(
        name="DHL",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
    )
    ShippingMethodChannelListing.objects.create(
        shipping_method=method,
        channel=channel_PLN,
        minimum_order_price=Money(0, channel_PLN.currency_code),
        price=Money(10, channel_PLN.currency_code),
        currency=channel_PLN.currency_code,
    )
    return method
