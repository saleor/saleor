import graphene

from ....shipping.error_codes import ShippingErrorCode
from ....shipping.models import ShippingMethodChannelListing
from ...tests.utils import assert_negative_positive_decimal_value, get_graphql_content

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
            channels
        }
        shippingMethod {
            name
            channelListings {
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


def test_shipping_method_channel_listing_create_as_staff_user(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
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

    assert shipping_method_data["channelListings"][1]["price"]["amount"] == price
    assert (
        shipping_method_data["channelListings"][1]["maximumOrderPrice"]["amount"]
        == max_value
    )
    assert (
        shipping_method_data["channelListings"][1]["minimumOrderPrice"]["amount"]
        == min_value
    )
    assert (
        shipping_method_data["channelListings"][1]["channel"]["slug"]
        == channel_PLN.slug
    )


def test_shipping_method_channel_listing_update_as_staff_user(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_USD,
):
    # given
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    min_value = 20
    max_value = 30

    variables = {
        "id": shipping_method_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "minimumOrderPrice": min_value,
                    "maximumOrderPrice": max_value,
                }
            ]
        },
    }
    channel_listing = ShippingMethodChannelListing.objects.get(
        shipping_method_id=shipping_method.pk, channel_id=channel_USD.id
    )

    assert channel_listing.price.amount == 10
    assert channel_listing.minimum_order_price.amount == 0
    assert channel_listing.maximum_order_price is None

    # when
    response = staff_api_client.post_graphql(
        SHIPPING_METHOD_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_shipping,),
    )
    content = get_graphql_content(response)

    data = content["data"]["shippingMethodChannelListingUpdate"]
    shipping_method_data = data["shippingMethod"]
    assert not data["shippingErrors"]
    assert shipping_method_data["name"] == shipping_method.name

    # then
    assert (
        shipping_method_data["channelListings"][0]["maximumOrderPrice"]["amount"]
        == max_value
    )
    assert (
        shipping_method_data["channelListings"][0]["minimumOrderPrice"]["amount"]
        == min_value
    )
    assert (
        shipping_method_data["channelListings"][0]["channel"]["slug"]
        == channel_USD.slug
    )

    channel_listing.refresh_from_db()

    assert channel_listing.price.amount == 10
    assert channel_listing.minimum_order_price.amount == min_value
    assert channel_listing.maximum_order_price.amount == max_value


def test_shipping_method_channel_listing_update_with_negative_price(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_PLN,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_shipping)
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
    )

    # then
    assert_negative_positive_decimal_value(response)


def test_shipping_method_channel_listing_update_with_negative_min_value(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_PLN,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_shipping)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    price = 10
    min_value = -2
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
    )

    # then
    assert_negative_positive_decimal_value(response)


def test_shipping_method_channel_listing_update_with_negative_max_value(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_PLN,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_shipping)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    price = 10
    max_value = -3

    variables = {
        "id": shipping_method_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "price": price,
                    "maximumOrderPrice": max_value,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        SHIPPING_METHOD_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
    )

    # then
    assert_negative_positive_decimal_value(response)


def test_shipping_method_channel_listing_update_with_max_less_than_min(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_PLN,
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
    assert data["shippingErrors"][0]["code"] == ShippingErrorCode.MAX_LESS_THAN_MIN.name
    assert data["shippingErrors"][0]["channels"] == [channel_id]


def test_shipping_method_channel_listing_create_without_price(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_PLN,
):
    # given
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    min_value = 10
    max_value = 15

    variables = {
        "id": shipping_method_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
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
    assert data["shippingErrors"][0]["code"] == ShippingErrorCode.REQUIRED.name
    assert data["shippingErrors"][0]["channels"] == [channel_id]


def test_shipping_method_channel_listing_update_with_to_many_decimal_places_in_price(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_PLN,
):
    # given
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    price = 10.1234
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
    assert data["shippingErrors"][0]["channels"] == [channel_id]


def test_shipping_method_channel_listing_update_with_to_many_decimal_places_in_min_val(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_PLN,
):
    # given
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    price = 10
    min_value = 2.1234
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
    assert data["shippingErrors"][0]["field"] == "minimumOrderPrice"
    assert data["shippingErrors"][0]["code"] == ShippingErrorCode.INVALID.name
    assert data["shippingErrors"][0]["channels"] == [channel_id]


def test_shipping_method_channel_listing_update_with_to_many_decimal_places_in_max_val(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_PLN,
):
    # given
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    price = 10
    min_value = 2
    max_value = 3.1234

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
    assert data["shippingErrors"][0]["code"] == ShippingErrorCode.INVALID.name
    assert data["shippingErrors"][0]["channels"] == [channel_id]
