import json
from unittest.mock import patch

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....shipping.error_codes import ShippingErrorCode
from .....shipping.models import ShippingMethodChannelListing
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import assert_negative_positive_decimal_value, get_graphql_content

SHIPPING_METHOD_CHANNEL_LISTING_UPDATE_MUTATION = """
mutation UpdateShippingMethodChannelListing(
    $id: ID!
    $input: ShippingMethodChannelListingInput!
) {
    shippingMethodChannelListingUpdate(id: $id, input: $input) {
        errors {
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
    shipping_method.shipping_zone.channels.add(channel_PLN)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
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
    assert not data["errors"]
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


def test_shipping_method_channel_listing_update_allow_to_set_null_for_limit_fields(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_PLN,
):
    # given
    shipping_method.shipping_zone.channels.add(channel_PLN)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    channel_listing = shipping_method.channel_listings.all()[0]
    channel = channel_listing.channel
    channel_id = graphene.Node.to_global_id("Channel", channel.id)
    channel_listing.minimum_order_price_amount = 2
    channel_listing.maximum_order_price_amount = 5
    channel_listing.save(
        update_fields=["minimum_order_price_amount", "maximum_order_price_amount"]
    )
    price = 3

    variables = {
        "id": shipping_method_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "price": price,
                    "minimumOrderPrice": None,
                    "maximumOrderPrice": None,
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
    channel_listing.refresh_from_db()

    # then
    data = content["data"]["shippingMethodChannelListingUpdate"]
    shipping_method_data = data["shippingMethod"]
    assert not data["errors"]
    assert shipping_method_data["channelListings"][0]["price"]["amount"] == price
    assert channel_listing.maximum_order_price_amount is None
    assert channel_listing.minimum_order_price_amount is None
    assert shipping_method_data["channelListings"][0]["maximumOrderPrice"] is None
    assert shipping_method_data["channelListings"][0]["minimumOrderPrice"] is None


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_shipping_method_channel_listing_create_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_PLN,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    shipping_method.shipping_zone.channels.add(channel_PLN)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
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
    assert not data["errors"]
    assert data["shippingMethod"]

    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": shipping_method_id,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.SHIPPING_PRICE_UPDATED,
        [any_webhook],
        shipping_method,
        SimpleLazyObject(lambda: staff_api_client.user),
        allow_replica=False,
    )


def test_shipping_method_channel_listing_update_as_staff_user(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_USD,
):
    # given
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
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
    assert not data["errors"]
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
    shipping_method.shipping_zone.channels.add(channel_PLN)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
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
    shipping_method.shipping_zone.channels.add(channel_PLN)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
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
    shipping_method.shipping_zone.channels.add(channel_PLN)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
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
    shipping_method.shipping_zone.channels.add(channel_PLN)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
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
    assert data["errors"][0]["field"] == "maximumOrderPrice"
    assert data["errors"][0]["code"] == ShippingErrorCode.MAX_LESS_THAN_MIN.name
    assert data["errors"][0]["channels"] == [channel_id]


def test_shipping_method_channel_listing_create_without_price(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_PLN,
):
    # given
    shipping_method.shipping_zone.channels.add(channel_PLN)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
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
    assert data["errors"][0]["field"] == "price"
    assert data["errors"][0]["code"] == ShippingErrorCode.REQUIRED.name
    assert data["errors"][0]["channels"] == [channel_id]


def test_shipping_method_channel_listing_update_with_to_many_decimal_places_in_price(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_PLN,
):
    # given
    shipping_method.shipping_zone.channels.add(channel_PLN)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
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
    assert data["errors"][0]["field"] == "price"
    assert data["errors"][0]["code"] == ShippingErrorCode.INVALID.name
    assert data["errors"][0]["channels"] == [channel_id]


def test_shipping_method_channel_listing_update_with_to_many_decimal_places_in_min_val(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_PLN,
):
    # given
    shipping_method.shipping_zone.channels.add(channel_PLN)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
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
    assert data["errors"][0]["field"] == "minimumOrderPrice"
    assert data["errors"][0]["code"] == ShippingErrorCode.INVALID.name
    assert data["errors"][0]["channels"] == [channel_id]


def test_shipping_method_channel_listing_update_with_to_many_decimal_places_in_max_val(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_PLN,
):
    # given
    shipping_method.shipping_zone.channels.add(channel_PLN)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
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
    assert data["errors"][0]["field"] == "maximumOrderPrice"
    assert data["errors"][0]["code"] == ShippingErrorCode.INVALID.name
    assert data["errors"][0]["channels"] == [channel_id]


def test_shipping_method_channel_listing_create_channel_not_valid(
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_PLN,
):
    # given
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
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

    # then
    assert data["errors"][0]["field"] == "addChannels"
    assert data["errors"][0]["code"] == ShippingErrorCode.INVALID.name
    assert data["errors"][0]["channels"] == [channel_id]


@patch(
    "saleor.graphql.shipping.mutations.shipping_method_channel_listing_update."
    "drop_invalid_shipping_methods_relations_for_given_channels.delay"
)
def test_shipping_method_channel_listing_update_remove_channels(
    mocked_drop_invalid_shipping_methods_relations,
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_USD,
):
    # given
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    assert shipping_method.channel_listings.count() == 1
    channel_listing = shipping_method.channel_listings.first()
    channel = channel_listing.channel
    channel_id = graphene.Node.to_global_id("Channel", channel.id)

    variables = {
        "id": shipping_method_id,
        "input": {"removeChannels": [channel_id]},
    }

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
    assert not data["errors"]
    assert shipping_method_data["name"] == shipping_method.name

    # then
    assert not shipping_method_data["channelListings"]
    with pytest.raises(channel_listing._meta.model.DoesNotExist):
        channel_listing.refresh_from_db()

    mocked_drop_invalid_shipping_methods_relations.assert_called_once_with(
        [shipping_method.pk], [str(channel.pk)]
    )


@pytest.mark.parametrize(
    ("price", "min_price", "max_price", "invalid_field"),
    [(10**9, 2, 3, "price"), (1, 2, 10**11, "maximumOrderPrice")],
)
def test_shipping_method_channel_listing_create_channel_max_value_validation(
    price,
    min_price,
    max_price,
    invalid_field,
    staff_api_client,
    shipping_method,
    permission_manage_shipping,
    channel_PLN,
):
    # given
    shipping_method.shipping_zone.channels.add(channel_PLN)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": shipping_method_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "price": price,
                    "minimumOrderPrice": min_price,
                    "maximumOrderPrice": max_price,
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
    assert data["errors"][0]["field"] == invalid_field
    assert data["errors"][0]["code"] == ShippingErrorCode.INVALID.name
