import pytest
from django_countries import countries

from ....core.prices import Money
from ....warehouse.models import Warehouse
from ...models import ShippingMethodChannelListing, ShippingMethodType, ShippingZone


@pytest.fixture
def shipping_zone(db, channel_USD, default_tax_class):  # pylint: disable=W0613
    shipping_zone = ShippingZone.objects.create(
        name="Europe", countries=[code for code, name in countries]
    )
    shipping_zone.channels.add(channel_USD)
    method = shipping_zone.shipping_methods.create(
        name="DHL",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
        tax_class=default_tax_class,
    )
    ShippingMethodChannelListing.objects.create(
        channel=channel_USD,
        currency=channel_USD.currency_code,
        shipping_method=method,
        minimum_order_price=Money(0, channel_USD.currency_code),
        price=Money(10, channel_USD.currency_code),
    )
    return shipping_zone


@pytest.fixture
def shipping_zone_JPY(shipping_zone, channel_JPY):
    shipping_zone.channels.add(channel_JPY)
    method = shipping_zone.shipping_methods.get()
    ShippingMethodChannelListing.objects.create(
        channel=channel_JPY,
        currency=channel_JPY.currency_code,
        shipping_method=method,
        minimum_order_price=Money(0, channel_JPY.currency_code),
        price=Money(700, channel_JPY.currency_code),
    )
    return shipping_zone


@pytest.fixture
def shipping_zones(db, channel_USD, channel_PLN):
    shipping_zone_poland, shipping_zone_usa = ShippingZone.objects.bulk_create(
        [
            ShippingZone(name="Poland", countries=["PL"]),
            ShippingZone(name="USA", countries=["US"]),
        ]
    )

    shipping_zone_poland.channels.add(channel_PLN, channel_USD)
    shipping_zone_usa.channels.add(channel_PLN, channel_USD)

    method = shipping_zone_poland.shipping_methods.create(
        name="DHL",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
    )
    second_method = shipping_zone_usa.shipping_methods.create(
        name="DHL",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
    )
    ShippingMethodChannelListing.objects.bulk_create(
        [
            ShippingMethodChannelListing(
                channel=channel_USD,
                shipping_method=method,
                minimum_order_price=Money(0, "USD"),
                price=Money(10, "USD"),
                currency=channel_USD.currency_code,
            ),
            ShippingMethodChannelListing(
                channel=channel_USD,
                shipping_method=second_method,
                minimum_order_price=Money(0, "USD"),
                currency=channel_USD.currency_code,
            ),
            ShippingMethodChannelListing(
                channel=channel_PLN,
                shipping_method=method,
                minimum_order_price=Money(0, "PLN"),
                price=Money(40, "PLN"),
                currency=channel_PLN.currency_code,
            ),
            ShippingMethodChannelListing(
                channel=channel_PLN,
                shipping_method=second_method,
                minimum_order_price=Money(0, "PLN"),
                currency=channel_PLN.currency_code,
            ),
        ]
    )
    return [shipping_zone_poland, shipping_zone_usa]


def chunks(it, n):
    for i in range(0, len(it), n):
        yield it[i : i + n]


@pytest.fixture
def shipping_zones_with_warehouses(address, channel_USD):
    zones = [ShippingZone(name=f"{i}_zone") for i in range(10)]
    warehouses = [Warehouse(slug=f"{i}_warehouse", address=address) for i in range(20)]
    warehouses = Warehouse.objects.bulk_create(warehouses)
    warehouses_in_batches = list(chunks(warehouses, 2))
    for i, zone in enumerate(ShippingZone.objects.bulk_create(zones)):
        zone.channels.add(channel_USD)
        for warehouse in warehouses_in_batches[i]:
            zone.warehouses.add(warehouse)
    return zones


@pytest.fixture
def shipping_zones_with_different_channels(db, channel_USD, channel_PLN):
    shipping_zone_poland, shipping_zone_usa = ShippingZone.objects.bulk_create(
        [
            ShippingZone(name="Poland", countries=["PL"]),
            ShippingZone(name="USA", countries=["US"]),
        ]
    )

    shipping_zone_poland.channels.add(channel_PLN, channel_USD)
    shipping_zone_usa.channels.add(channel_USD)

    method = shipping_zone_poland.shipping_methods.create(
        name="DHL",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
    )
    second_method = shipping_zone_usa.shipping_methods.create(
        name="DHL",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
    )
    ShippingMethodChannelListing.objects.bulk_create(
        [
            ShippingMethodChannelListing(
                channel=channel_USD,
                shipping_method=method,
                minimum_order_price=Money(0, "USD"),
                price=Money(10, "USD"),
                currency=channel_USD.currency_code,
            ),
            ShippingMethodChannelListing(
                channel=channel_USD,
                shipping_method=second_method,
                minimum_order_price=Money(0, "USD"),
                currency=channel_USD.currency_code,
            ),
            ShippingMethodChannelListing(
                channel=channel_PLN,
                shipping_method=method,
                minimum_order_price=Money(0, "PLN"),
                price=Money(40, "PLN"),
                currency=channel_PLN.currency_code,
            ),
            ShippingMethodChannelListing(
                channel=channel_PLN,
                shipping_method=second_method,
                minimum_order_price=Money(0, "PLN"),
                currency=channel_PLN.currency_code,
            ),
        ]
    )
    return [shipping_zone_poland, shipping_zone_usa]


@pytest.fixture
def shipping_zone_without_countries(db, channel_USD):  # pylint: disable=W0613
    shipping_zone = ShippingZone.objects.create(name="Europe", countries=[])
    method = shipping_zone.shipping_methods.create(
        name="DHL",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
    )
    ShippingMethodChannelListing.objects.create(
        channel=channel_USD,
        shipping_method=method,
        minimum_order_price=Money(0, "USD"),
        price=Money(10, "USD"),
    )
    return shipping_zone
