import graphene

from ...tests.utils import get_graphql_content

SHIPPING_METHOD_CHANNEL_LISTING_UPDATE_MUTATION = """
mutation UpdateShippingMethodChannelListing(
    $id: ID!
    $input: ShippingMethodChannelListingUpdateInput!
) {
    shippingMethodChannelListingUpdate(id: $id, input: $input) {
        shippingErrors {
            field
            message
            code
        }
        shippingMethod {
            name
            channels {
                price
                minValue
                maxValue
                channel {
                    slug
                }
            }
        }
    }
}
"""


def test_shipping_method_channel_listing_update_as_staff_user(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_USD,
    channel_PLN,
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
                    "minValue": min_value,
                    "maxValue": max_value,
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
    breakpoint()

    # then
    data = content["data"]["shippingMethodChannelListingUpdate"]
    shipping_method_data = data["shippingMethod"]
    # assert not data["productsErrors"]
    assert shipping_method_data["name"] == shipping_method.name
    assert shipping_method_data["channels"][0]["price"] is None
    assert shipping_method_data["channels"][0]["minValue"] is None
    assert shipping_method_data["channels"][0]["maxValue"] is None
    assert shipping_method_data["channels"][0]["channel"]["slug"] == channel_USD.slug
    assert shipping_method_data["channels"][1]["price"] == price
    assert shipping_method_data["channels"][1]["minValue"] == min_value
    assert shipping_method_data["channels"][1]["maxValue"] == max_value
    assert shipping_method_data["channels"][1]["channel"]["slug"] == channel_PLN.slug
