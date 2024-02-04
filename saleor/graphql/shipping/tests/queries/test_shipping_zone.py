from unittest.mock import Mock

import graphene
from django.contrib.sites.models import Site
from measurement.measures import Weight

from .....core.units import WeightUnits
from ....shipping.resolvers import resolve_price_range
from ....tests.utils import get_graphql_content, get_graphql_content_from_response

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
    info_mock = Mock()
    info_mock.side_effect = {"context": Mock()}
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
    price_range = resolve_price_range(info_mock, channel_slug=channel_USD.slug)
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
    info_mock = Mock()
    info_mock.side_effect = {"context": Mock()}
    shipping = shipping_zone
    shipping_method = shipping.shipping_methods.first()
    shipping_method.minimum_order_weight = Weight(kg=1)
    shipping_method.maximum_order_weight = Weight(kg=10)
    shipping_method.save(update_fields=["minimum_order_weight", "maximum_order_weight"])

    site_settings.default_weight_unit = WeightUnits.G
    site_settings.save(update_fields=["default_weight_unit"])
    Site.objects.clear_cache()

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
    price_range = resolve_price_range(info_mock, channel_slug=channel_USD.slug)
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
    # given
    id = "bh/"
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        SHIPPING_ZONE_QUERY, variables, permissions=[permission_manage_shipping]
    )

    # then
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert (
        content["errors"][0]["message"] == f"Invalid ID: {id}. Expected: ShippingZone."
    )
    assert content["data"]["shippingZone"] is None


def test_staff_query_shipping_zone_object_given_id_does_not_exists(
    staff_api_client, permission_manage_shipping
):
    # given
    variables = {"id": graphene.Node.to_global_id("Order", -1)}

    # when
    response = staff_api_client.post_graphql(
        SHIPPING_ZONE_QUERY, variables, permissions=[permission_manage_shipping]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["shippingZone"] is None


SHIPPING_METHOD_TAX_CLASS_QUERY = """
    query ShippingQuery($id: ID!) {
        shippingZone(id: $id) {
            name
            shippingMethods {
                id
                taxClass {
                    id
                }
            }
        }
    }
"""


def test_shipping_method_tax_class_query_by_app(
    app_api_client, shipping_zone, permission_manage_shipping
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("ShippingZone", shipping_zone.id),
    }

    # when
    app_api_client.app.permissions.add(permission_manage_shipping)
    response = app_api_client.post_graphql(SHIPPING_METHOD_TAX_CLASS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]
    assert data["shippingZone"]["shippingMethods"][0]["taxClass"]["id"]


def test_shipping_method_tax_class_query_by_staff(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("ShippingZone", shipping_zone.id),
    }

    # when
    staff_api_client.user.user_permissions.add(permission_manage_shipping)
    response = staff_api_client.post_graphql(SHIPPING_METHOD_TAX_CLASS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]
    assert data["shippingZone"]["shippingMethods"][0]["taxClass"]["id"]
