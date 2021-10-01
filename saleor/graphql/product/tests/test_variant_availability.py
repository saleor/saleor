import graphene
from django.test import override_settings
from django_countries import countries

from ....shipping.models import ShippingZone
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


@override_settings(MAX_CHECKOUT_LINE_QUANTITY=15)
def test_variant_quantity_available_with_max(
    api_client, variant_with_many_stocks, settings, channel_USD
):
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
    assert variant_data["deprecatedByCountry"] == settings.MAX_CHECKOUT_LINE_QUANTITY
    assert variant_data["byAddress"] == settings.MAX_CHECKOUT_LINE_QUANTITY


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


@override_settings(MAX_CHECKOUT_LINE_QUANTITY=15)
def test_variant_quantity_available_without_inventory_tracking(
    api_client, variant_with_many_stocks, settings, channel_USD
):
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
    assert variant_data["deprecatedByCountry"] == settings.MAX_CHECKOUT_LINE_QUANTITY
    assert variant_data["byAddress"] == settings.MAX_CHECKOUT_LINE_QUANTITY


@override_settings(MAX_CHECKOUT_LINE_QUANTITY=15)
def test_variant_quantity_available_without_inventory_tracking_and_stocks(
    api_client, variant, settings, channel_USD
):
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
    assert variant_data["deprecatedByCountry"] == settings.MAX_CHECKOUT_LINE_QUANTITY
    assert variant_data["byAddress"] == settings.MAX_CHECKOUT_LINE_QUANTITY


@override_settings(MAX_CHECKOUT_LINE_QUANTITY=15)
def test_variant_quantity_available_preorder_with_channel_threshold(
    api_client,
    preorder_variant_channel_threshold,
    channel_USD,
):
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


@override_settings(MAX_CHECKOUT_LINE_QUANTITY=15)
def test_variant_quantity_available_preorder_with_global_threshold(
    api_client, preorder_variant_global_threshold, channel_USD
):
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


@override_settings(MAX_CHECKOUT_LINE_QUANTITY=15)
def test_variant_quantity_available_preorder_without_threshold(
    api_client, preorder_variant_global_threshold, settings, channel_USD
):
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
    assert variant_data["deprecatedByCountry"] == settings.MAX_CHECKOUT_LINE_QUANTITY
    assert variant_data["byAddress"] == settings.MAX_CHECKOUT_LINE_QUANTITY
