import graphene

from ....shipping.error_codes import ShippingErrorCode
from ...tests.utils import get_graphql_content

SHIPPING_METHOD_CHANNEL_LISTING_UPDATE_MUTATION = """
mutation UpdateShippingMethodChannelListing(
    $id: ID!
    $input: ShippingMethodChannelListingInput!
) {
    shippingMethodChannelListingUpdate(id: $id, input: $input) {
        shippingErrors {
            field
            message
            code
        }
        shippingMethod {
            name
            channelListing {
                price {
                    amount
                }
                maximumOrderPrice {
                    amount
                }
                minimumOrderPrice {
                    amount
                }
                channel {
                    slug
                }
            }
        }
    }
}
"""


def test_shipping_method_channel_listing_update_as_staff_user(
    staff_api_client, shipping_method, permission_manage_shipping, channel_PLN,
):
    # given
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    price = 1
    min_value = 2
    max_value = 3

    variables = {
        "id": shipping_method_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "price": price,
                    "minimumOrderPrice": min_value,
                    "maximumOrderPrice": max_value,
                }
            ]
        },
    }

    # when

    response = staff_api_client.post_graphql(
        SHIPPING_METHOD_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_shipping,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["shippingMethodChannelListingUpdate"]
    shipping_method_data = data["shippingMethod"]
    assert not data["shippingErrors"]
    assert shipping_method_data["name"] == shipping_method.name

    assert shipping_method_data["channelListing"][1]["price"]["amount"] == price
    assert (
        shipping_method_data["channelListing"][1]["maximumOrderPrice"]["amount"]
        == max_value
    )
    assert (
        shipping_method_data["channelListing"][1]["minimumOrderPrice"]["amount"]
        == min_value
    )
    assert (
        shipping_method_data["channelListing"][1]["channel"]["slug"] == channel_PLN.slug
    )


def test_shipping_method_channel_listing_update_with_negative_price(
    staff_api_client, shipping_method, permission_manage_shipping, channel_PLN,
):
    # given
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    price = -10
    min_value = 2
    max_value = 3

    variables = {
        "id": shipping_method_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "price": price,
                    "minimumOrderPrice": min_value,
                    "maximumOrderPrice": max_value,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        SHIPPING_METHOD_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_shipping,),
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingMethodChannelListingUpdate"]

    # then
    assert data["shippingErrors"][0]["field"] == "price"
    assert data["shippingErrors"][0]["code"] == ShippingErrorCode.INVALID.name


def test_shipping_method_channel_listing_update_with_max_less_than_min(
    staff_api_client, shipping_method, permission_manage_shipping, channel_PLN,
):
    # given
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    price = 1
    min_value = 20
    max_value = 15

    variables = {
        "id": shipping_method_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "price": price,
                    "minimumOrderPrice": min_value,
                    "maximumOrderPrice": max_value,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        SHIPPING_METHOD_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_shipping,),
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingMethodChannelListingUpdate"]

    # then
    assert data["shippingErrors"][0]["field"] == "maximumOrderPrice"
    assert data["shippingErrors"][0]["field"] == "maximumOrderPrice"
