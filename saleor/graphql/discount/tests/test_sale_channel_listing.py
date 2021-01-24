from unittest.mock import patch

import graphene

from ....discount.error_codes import DiscountErrorCode
from ....discount.models import SaleChannelListing
from ...tests.utils import assert_negative_positive_decimal_value, get_graphql_content

SALE_CHANNEL_LISTING_UPDATE_MUTATION = """
mutation UpdateSaleChannelListing(
    $id: ID!
    $input: SaleChannelListingInput!
) {
    saleChannelListingUpdate(id: $id, input: $input) {
        discountErrors {
            field
            message
            code
            channels
        }
        sale {
            name
            channelListings {
                discountValue
                channel {
                    slug
                }
            }
        }
    }
}
"""


@patch(
    "saleor.graphql.discount.mutations"
    ".update_products_discounted_prices_of_discount_task"
)
def test_sale_channel_listing_create_as_staff_user(
    mock_update_discounted_prices_of_discount_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_PLN,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    discounted = 1.12

    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [{"channelId": channel_id, "discountValue": discounted}]
        },
    }

    # when

    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["saleChannelListingUpdate"]
    shipping_method_data = data["sale"]
    assert not data["discountErrors"]
    assert shipping_method_data["name"] == sale.name

    assert shipping_method_data["channelListings"][1]["discountValue"] == discounted
    assert (
        shipping_method_data["channelListings"][1]["channel"]["slug"]
        == channel_PLN.slug
    )
    mock_update_discounted_prices_of_discount_task.delay.assert_called_once_with(
        sale.pk,
    )


@patch(
    "saleor.graphql.discount.mutations"
    ".update_products_discounted_prices_of_discount_task"
)
def test_sale_channel_listing_update_as_staff_user(
    mock_update_discounted_prices_of_discount_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    discounted = 10.11

    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [{"channelId": channel_id, "discountValue": discounted}]
        },
    }
    channel_listing = SaleChannelListing.objects.get(
        sale_id=sale.pk, channel_id=channel_USD.id
    )
    assert channel_listing.discount_value == 5

    # when

    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["saleChannelListingUpdate"]
    shipping_method_data = data["sale"]
    assert not data["discountErrors"]

    assert shipping_method_data["channelListings"][0]["discountValue"] == discounted
    mock_update_discounted_prices_of_discount_task.delay.assert_called_once_with(
        sale.pk,
    )


def test_sale_channel_listing_update_with_negative_discounted_value(
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_USD,
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    discounted_value = -10

    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [
                {"channelId": channel_id, "discountValue": discounted_value}
            ]
        },
    }
    channel_listing = SaleChannelListing.objects.get(
        sale_id=sale.pk, channel_id=channel_USD.id
    )
    assert channel_listing.discount_value == 5

    # when
    staff_api_client.user.user_permissions.add(permission_manage_discounts)

    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
    )
    assert_negative_positive_decimal_value(response)


def test_sale_channel_listing_update_duplicated_ids_in_add_and_remove(
    staff_api_client, sale, permission_manage_discounts, channel_USD
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    discounted = 10.11
    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [{"channelId": channel_id, "discountValue": discounted}],
            "removeChannels": [channel_id],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["saleChannelListingUpdate"]["discountErrors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "input"
    assert errors[0]["code"] == DiscountErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["channels"] == [channel_id]


def test_sale_channel_listing_update_duplicated_channel_in_add(
    staff_api_client, sale, permission_manage_discounts, channel_USD
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    discounted = 10.11
    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [
                {"channelId": channel_id, "discountValue": discounted},
                {"channelId": channel_id, "discountValue": discounted},
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["saleChannelListingUpdate"]["discountErrors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "addChannels"
    assert errors[0]["code"] == DiscountErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["channels"] == [channel_id]


def test_sale_channel_listing_update_duplicated_channel_in_remove(
    staff_api_client, sale, permission_manage_discounts, channel_USD
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": sale_id,
        "input": {"removeChannels": [channel_id, channel_id]},
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["saleChannelListingUpdate"]["discountErrors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "removeChannels"
    assert errors[0]["code"] == DiscountErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["channels"] == [channel_id]


def test_sale_channel_listing_update_with_invalid_decimal_places(
    staff_api_client, sale, permission_manage_discounts, channel_USD
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)
    discounted = 1.123
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": sale_id,
        "input": {
            "addChannels": [{"channelId": channel_id, "discountValue": discounted}],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)
    # then
    errors = content["data"]["saleChannelListingUpdate"]["discountErrors"]

    assert len(errors) == 1
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name
    assert errors[0]["field"] == "input"
    assert errors[0]["channels"] == [channel_id]
