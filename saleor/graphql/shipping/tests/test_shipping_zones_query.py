import graphene
import pytest
from measurement.measures import Weight

from ....core.units import WeightUnits
from ...shipping.resolvers import resolve_price_range
from ...tests.utils import get_graphql_content, get_graphql_content_from_response

SHIPPING_ZONE_QUERY = """
    query ShippingQuery($id: ID!, $channel: String,) {
        shippingZone(id: $id, channel:$channel) {
            name
            shippingMethods {
                postalCodeRules {
                    start
                    end
                }
                channelListings {
                    id
                    price {
                        amount
                    }
                    maximumOrderPrice {
                        amount
                    }
                    minimumOrderPrice {
                        amount
                    }
                }
                minimumOrderWeight {
                    value
                    unit
                }
                maximumOrderWeight {
                    value
                    unit
                }
            }
            priceRange {
                start {
                    amount
                }
                stop {
                    amount
                }
            }
        }
    }
"""


def test_shipping_zone_query(
    staff_api_client, shipping_zone, permission_manage_shipping, channel_USD
):
    # given
    shipping = shipping_zone
    method = shipping.shipping_methods.first()
    code = method.postal_code_rules.create(start="HB2", end="HB6")
    query = SHIPPING_ZONE_QUERY
    ID = graphene.Node.to_global_id("ShippingZone", shipping.id)
    variables = {"id": ID, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )

    # then
    content = get_graphql_content(response)
    shipping_data = content["data"]["shippingZone"]
    assert shipping_data["name"] == shipping.name
    num_of_shipping_methods = shipping_zone.shipping_methods.count()
    assert len(shipping_data["shippingMethods"]) == num_of_shipping_methods
    assert shipping_data["shippingMethods"][0]["postalCodeRules"] == [
        {"start": code.start, "end": code.end}
    ]
    price_range = resolve_price_range(channel_slug=channel_USD.slug)
    data_price_range = shipping_data["priceRange"]
    assert data_price_range["start"]["amount"] == price_range.start.amount
    assert data_price_range["stop"]["amount"] == price_range.stop.amount


def test_shipping_zone_query_weights_returned_in_default_unit(
    staff_api_client,
    shipping_zone,
    permission_manage_shipping,
    site_settings,
    channel_USD,
):
    # given
    shipping = shipping_zone
    shipping_method = shipping.shipping_methods.first()
    shipping_method.minimum_order_weight = Weight(kg=1)
    shipping_method.maximum_order_weight = Weight(kg=10)
    shipping_method.save(update_fields=["minimum_order_weight", "maximum_order_weight"])

    site_settings.default_weight_unit = WeightUnits.G
    site_settings.save(update_fields=["default_weight_unit"])

    query = SHIPPING_ZONE_QUERY
    ID = graphene.Node.to_global_id("ShippingZone", shipping.id)
    variables = {"id": ID, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )

    # then
    content = get_graphql_content(response)

    shipping_data = content["data"]["shippingZone"]
    assert shipping_data["name"] == shipping.name
    num_of_shipping_methods = shipping_zone.shipping_methods.count()
    assert len(shipping_data["shippingMethods"]) == num_of_shipping_methods
    price_range = resolve_price_range(channel_slug=channel_USD.slug)
    data_price_range = shipping_data["priceRange"]
    assert data_price_range["start"]["amount"] == price_range.start.amount
    assert data_price_range["stop"]["amount"] == price_range.stop.amount
    assert shipping_data["shippingMethods"][0]["minimumOrderWeight"]["value"] == 1000
    assert (
        shipping_data["shippingMethods"][0]["minimumOrderWeight"]["unit"]
        == WeightUnits.G.upper()
    )
    assert shipping_data["shippingMethods"][0]["maximumOrderWeight"]["value"] == 10000
    assert (
        shipping_data["shippingMethods"][0]["maximumOrderWeight"]["unit"]
        == WeightUnits.G.upper()
    )


def test_staff_query_shipping_zone_by_invalid_id(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        SHIPPING_ZONE_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["shippingZone"] is None


def test_staff_query_shipping_zone_object_given_id_does_not_exists(
    staff_api_client, permission_manage_shipping
):
    variables = {"id": graphene.Node.to_global_id("Order", -1)}
    response = staff_api_client.post_graphql(
        SHIPPING_ZONE_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    assert content["data"]["shippingZone"] is None


MULTIPLE_SHIPPING_QUERY = """
    query MultipleShippings($channel: String) {
        shippingZones(first: 100, channel: $channel) {
            edges {
                node {
                    id
                    name
                    priceRange {
                        start {
                            amount
                        }
                        stop {
                            amount
                        }
                    }
                    shippingMethods {
                        channelListings {
                            price {
                                amount
                            }
                        }
                    }
                    warehouses {
                        id
                        name
                    }
                }
            }
            totalCount
        }
    }
"""


def test_shipping_zones_query(
    staff_api_client,
    shipping_zone,
    permission_manage_shipping,
    permission_manage_products,
    channel_USD,
):

    num_of_shippings = shipping_zone._meta.model.objects.count()
    variables = {"channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        MULTIPLE_SHIPPING_QUERY,
        variables,
        permissions=[permission_manage_shipping, permission_manage_products],
    )
    content = get_graphql_content(response)
    assert content["data"]["shippingZones"]["totalCount"] == num_of_shippings


def test_shipping_methods_query_with_channel(
    staff_api_client,
    shipping_zone,
    shipping_method_channel_PLN,
    permission_manage_shipping,
    permission_manage_products,
    channel_USD,
):
    shipping_zone.shipping_methods.add(shipping_method_channel_PLN)
    variables = {"channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        MULTIPLE_SHIPPING_QUERY,
        variables,
        permissions=[permission_manage_shipping, permission_manage_products],
    )
    content = get_graphql_content(response)
    assert (
        len(content["data"]["shippingZones"]["edges"][0]["node"]["shippingMethods"])
        == 1
    )


def test_shipping_methods_query(
    staff_api_client,
    shipping_zone,
    shipping_method_channel_PLN,
    permission_manage_shipping,
    permission_manage_products,
    channel_USD,
):
    shipping_zone.shipping_methods.add(shipping_method_channel_PLN)
    response = staff_api_client.post_graphql(
        MULTIPLE_SHIPPING_QUERY,
        permissions=[permission_manage_shipping, permission_manage_products],
    )
    content = get_graphql_content(response)
    assert (
        len(content["data"]["shippingZones"]["edges"][0]["node"]["shippingMethods"])
        == 2
    )


QUERY_SHIPPING_ZONES_WITH_FILTER = """
    query ShippingZones($filter: ShippingZoneFilterInput) {
        shippingZones(filter: $filter, first: 100) {
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "lookup, expected_zones",
    [
        ("Poland", {"Poland"}),
        ("pol", {"Poland"}),
        ("USA", {"USA"}),
        ("us", {"USA"}),
        ("", {"Poland", "USA"}),
    ],
)
def test_query_shipping_zone_search_by_name(
    staff_api_client, shipping_zones, permission_manage_shipping, lookup, expected_zones
):
    variables = {"filter": {"search": lookup}}
    response = staff_api_client.post_graphql(
        QUERY_SHIPPING_ZONES_WITH_FILTER,
        variables=variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZones"]["edges"]

    assert len(data) == len(expected_zones)
    assert {zone["node"]["name"] for zone in data} == expected_zones


def test_query_shipping_zone_search_by_channels(
    staff_api_client, shipping_zones, permission_manage_shipping, channel_USD
):
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    shipping_zone_usd = shipping_zones[0]
    shipping_zone_usd_id = graphene.Node.to_global_id(
        "ShippingZone", shipping_zone_usd.id
    )
    variables = {"filter": {"channels": [channel_id]}}
    response = staff_api_client.post_graphql(
        QUERY_SHIPPING_ZONES_WITH_FILTER,
        variables=variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZones"]["edges"]

    assert data[0]["node"]["name"] == shipping_zone_usd.name
    assert data[0]["node"]["id"] == shipping_zone_usd_id


def test_query_shipping_zone_search_by_channels_no_matter_of_input(
    staff_api_client,
    shipping_zones_with_different_channels,
    permission_manage_shipping,
    channel_USD,
    channel_PLN,
):
    # given
    shipping_zones = shipping_zones_with_different_channels
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    shipping_zone_pln = shipping_zones[0]
    shipping_zone_pln_id = graphene.Node.to_global_id(
        "ShippingZone", shipping_zone_pln.id
    )
    variables = {"filter": {"channels": [channel_id]}}
    # when
    response = staff_api_client.post_graphql(
        QUERY_SHIPPING_ZONES_WITH_FILTER,
        variables=variables,
        permissions=[permission_manage_shipping],
    )
    # then
    content = get_graphql_content(response)
    data = content["data"]["shippingZones"]["edges"]

    assert len(data) == 1
    assert data[0]["node"]["name"] == shipping_zone_pln.name
    assert data[0]["node"]["id"] == shipping_zone_pln_id
