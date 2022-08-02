import warnings
from datetime import timedelta

import graphene
import pytest
from django.utils import timezone
from django_countries import countries

from ....channel.utils import DEPRECATION_WARNING_MESSAGE
from ....shipping.models import ShippingZone
from ....warehouse.models import PreorderReservation, Reservation
from ...tests.utils import get_graphql_content

COUNTRY_CODE = "US"

QUERY_QUANTITY_AVAILABLE = """
    query variantAvailability($id: ID!, $channel: String) {
        productVariant(id: $id, channel: $channel) {
            quantityAvailable
        }
    }
    """


def test_variant_quantity_available_without_country_code(
    api_client, variant_with_many_stocks, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_QUANTITY_AVAILABLE, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == 7


def test_variant_quantity_available_without_country_code_or_channel(
    api_client, variant_with_many_stocks, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk)
    }
    with warnings.catch_warnings(record=True) as warns:
        response = api_client.post_graphql(QUERY_QUANTITY_AVAILABLE, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == 7
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_variant_quantity_available_when_one_stock_is_exceeded(
    api_client, variant_with_many_stocks, channel_USD
):
    # make first stock exceeded
    stock = variant_with_many_stocks.stocks.first()
    stock.quantity = -99
    stock.save()

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_QUANTITY_AVAILABLE, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == 3


def test_variant_quantity_available_without_country_code_and_no_channel_shipping_zones(
    api_client, variant_with_many_stocks, channel_USD
):
    channel_USD.shipping_zones.clear()
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_QUANTITY_AVAILABLE, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == 0


QUERY_VARIANT_AVAILABILITY = """
    query variantAvailability(
        $id: ID!, $country: CountryCode, $address: AddressInput, $channel: String
    ) {
        productVariant(id: $id, channel: $channel) {
            deprecatedByCountry: quantityAvailable(countryCode: $country)
            byAddress: quantityAvailable(address: $address)
        }
    }
"""


def test_variant_quantity_available_with_country_code(
    api_client, variant_with_many_stocks, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "address": {"country": COUNTRY_CODE},
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 7
    assert variant_data["byAddress"] == 7


def test_variant_quantity_available_with_country_code_no_channel_shipping_zones(
    api_client, variant_with_many_stocks, channel_USD
):
    channel_USD.shipping_zones.clear()
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "address": {"country": COUNTRY_CODE},
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 0
    assert variant_data["byAddress"] == 0


def test_variant_quantity_available_with_country_code_only_one_available_warehouse(
    api_client, variant_with_many_stocks, channel_USD, warehouses_with_shipping_zone
):
    shipping_zone = ShippingZone.objects.create(
        name="Test", countries=[code for code, name in countries]
    )
    warehouses_with_shipping_zone[0].shipping_zones.set([shipping_zone])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "address": {"country": COUNTRY_CODE},
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 3
    assert variant_data["byAddress"] == 3


def test_variant_quantity_available_with_null_as_country_code(
    api_client, variant_with_many_stocks, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": None,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 7
    assert variant_data["byAddress"] == 7


def test_variant_quantity_available_with_max(
    api_client, variant_with_many_stocks, site_settings, channel_USD
):
    site_settings.limit_quantity_per_checkout = 15
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    stock = variant_with_many_stocks.stocks.first()
    stock.quantity = 16
    stock.save(update_fields=["quantity"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert (
        variant_data["deprecatedByCountry"] == site_settings.limit_quantity_per_checkout
    )
    assert variant_data["byAddress"] == site_settings.limit_quantity_per_checkout


def test_variant_quantity_available_without_stocks(
    api_client, variant_with_many_stocks, channel_USD
):
    variant_with_many_stocks.stocks.all().delete()
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 0
    assert variant_data["byAddress"] == 0


def test_variant_quantity_available_with_allocations(
    api_client,
    variant_with_many_stocks,
    order_line_with_allocation_in_many_stocks,
    order_line_with_one_allocation,
    channel_USD,
):
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 3
    assert variant_data["byAddress"] == 3


def test_variant_quantity_available_with_enabled_reservations(
    site_settings_with_reservations,
    api_client,
    checkout_line_with_reservation_in_many_stocks,
    channel_USD,
):
    variant = checkout_line_with_reservation_in_many_stocks.variant
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 4
    assert variant_data["byAddress"] == 4


def test_variant_quantity_available_with_enabled_expired_reservations(
    site_settings_with_reservations,
    api_client,
    checkout_line_with_reservation_in_many_stocks,
    channel_USD,
):
    Reservation.objects.update(reserved_until=timezone.now() - timedelta(minutes=2))
    variant = checkout_line_with_reservation_in_many_stocks.variant
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 7
    assert variant_data["byAddress"] == 7


def test_variant_quantity_available_with_disabled_reservations(
    api_client,
    checkout_line_with_reservation_in_many_stocks,
    channel_USD,
):
    variant = checkout_line_with_reservation_in_many_stocks.variant
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 7
    assert variant_data["byAddress"] == 7


def test_variant_quantity_available_without_inventory_tracking(
    api_client, variant_with_many_stocks, site_settings, channel_USD
):
    site_settings.limit_quantity_per_checkout = 15
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    variant_with_many_stocks.track_inventory = False
    variant_with_many_stocks.save(update_fields=["track_inventory"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert (
        variant_data["deprecatedByCountry"] == site_settings.limit_quantity_per_checkout
    )
    assert variant_data["byAddress"] == site_settings.limit_quantity_per_checkout


def test_variant_quantity_available_without_inventory_tracking_no_global_limit(
    api_client, variant_with_many_stocks, site_settings, channel_USD
):
    site_settings.limit_quantity_per_checkout = None
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    variant_with_many_stocks.track_inventory = False
    variant_with_many_stocks.save(update_fields=["track_inventory"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] is None
    assert variant_data["byAddress"] is None


def test_variant_quantity_available_without_inventory_tracking_and_stocks(
    api_client, variant, site_settings, channel_USD
):
    site_settings.limit_quantity_per_checkout = 15
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    variant.track_inventory = False
    variant.save(update_fields=["track_inventory"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert (
        variant_data["deprecatedByCountry"] == site_settings.limit_quantity_per_checkout
    )
    assert variant_data["byAddress"] == site_settings.limit_quantity_per_checkout


def test_variant_qty_available_without_inventory_tracking_and_stocks_no_global_limit(
    api_client, variant, site_settings, channel_USD
):
    site_settings.limit_quantity_per_checkout = None
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    variant.track_inventory = False
    variant.save(update_fields=["track_inventory"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] is None
    assert variant_data["byAddress"] is None


@pytest.mark.parametrize("global_limit", [15, None])
def test_variant_quantity_available_preorder_with_channel_threshold(
    api_client,
    site_settings,
    preorder_variant_channel_threshold,
    channel_USD,
    global_limit,
):
    site_settings.limit_quantity_per_checkout = global_limit
    site_settings.save(update_fields=["limit_quantity_per_checkout"])

    variant = preorder_variant_channel_threshold
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    channel_listing = variant.channel_listings.get()
    assert (
        variant_data["deprecatedByCountry"]
        == channel_listing.preorder_quantity_threshold
    )
    assert variant_data["byAddress"] == channel_listing.preorder_quantity_threshold


def test_variant_quantity_available_preorder_without_reservations(
    site_settings_with_reservations,
    api_client,
    preorder_variant_channel_threshold,
    channel_USD,
):
    site_settings_with_reservations.limit_quantity_per_checkout = 15
    site_settings_with_reservations.save(update_fields=["limit_quantity_per_checkout"])

    variant = preorder_variant_channel_threshold
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    channel_listing = variant.channel_listings.get()
    assert (
        variant_data["deprecatedByCountry"]
        == channel_listing.preorder_quantity_threshold
    )
    assert variant_data["byAddress"] == channel_listing.preorder_quantity_threshold


def test_variant_quantity_available_preorder_with_channel_threshold_and_reservation(
    site_settings_with_reservations,
    api_client,
    preorder_variant_channel_threshold,
    checkout_line_with_reserved_preorder_item,
    channel_USD,
):
    site_settings_with_reservations.limit_quantity_per_checkout = 15
    site_settings_with_reservations.save(update_fields=["limit_quantity_per_checkout"])

    variant = preorder_variant_channel_threshold
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    channel_listing = variant.channel_listings.get()

    reservation = PreorderReservation.objects.all().first()
    available_quantity = channel_listing.preorder_quantity_threshold
    available_quantity -= reservation.quantity_reserved

    assert variant_data["deprecatedByCountry"] == available_quantity
    assert variant_data["byAddress"] == available_quantity


@pytest.mark.parametrize("global_limit", [15, None])
def test_variant_quantity_available_preorder_with_global_threshold(
    api_client,
    site_settings,
    preorder_variant_global_threshold,
    channel_USD,
    global_limit,
):
    site_settings.limit_quantity_per_checkout = global_limit
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    variant = preorder_variant_global_threshold
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == variant.preorder_global_threshold
    assert variant_data["byAddress"] == variant.preorder_global_threshold


def test_variant_quantity_available_preorder_with_global_threshold_and_reservations(
    site_settings_with_reservations,
    api_client,
    checkout_line_with_reserved_preorder_item,
    channel_USD,
):
    site_settings_with_reservations.limit_quantity_per_checkout = 15
    site_settings_with_reservations.save(update_fields=["limit_quantity_per_checkout"])

    variant = checkout_line_with_reserved_preorder_item.variant
    variant.channel_listings.update(preorder_quantity_threshold=None)
    variant.preorder_global_threshold = 10
    variant.save()

    reservation = PreorderReservation.objects.all().first()
    available_quantity = (
        variant.preorder_global_threshold - reservation.quantity_reserved
    )

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == available_quantity
    assert variant_data["byAddress"] == available_quantity


@pytest.mark.parametrize("global_limit", [15, None])
def test_variant_quantity_available_preorder_without_threshold(
    api_client,
    preorder_variant_global_threshold,
    site_settings,
    channel_USD,
    global_limit,
):
    site_settings.limit_quantity_per_checkout = global_limit
    site_settings.save(update_fields=["limit_quantity_per_checkout"])

    variant = preorder_variant_global_threshold
    variant.preorder_global_threshold = None
    variant.save(update_fields=["preorder_global_threshold"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]

    assert (
        variant_data["deprecatedByCountry"] == site_settings.limit_quantity_per_checkout
    )
    assert variant_data["byAddress"] == site_settings.limit_quantity_per_checkout


def test_variant_quantity_available_preorder_without_channel(
    api_client,
    site_settings,
    preorder_variant_global_threshold,
    channel_USD,
):
    site_settings.limit_quantity_per_checkout = 15
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    variant = preorder_variant_global_threshold
    variant.channel_listings.all().delete()
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    assert not content["data"]["productVariant"]
