from unittest.mock import patch

import graphene
import pytest

from .....product.error_codes import ProductErrorCode
from .....product.models import ProductVariantChannelListing
from ....product.mutations.channels import AVAILABILITY_UPDATE_MAX_ITEMS
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

PRODUCT_VARIANT_CHANNEL_LISTING_AVAILABILITY_UPDATE_MUTATION = """
mutation UpdateAvailability(
    $id: ID,
    $sku: String,
    $input: [ProductVariantChannelListingAvailabilityInput!]!
) {
    productVariantChannelListingAvailabilityUpdate(
        id: $id, sku: $sku, input: $input
    ) {
        errors {
            field
            message
            code
            channels
        }
        variant {
            id
            channelListings {
                channel {
                    slug
                }
                isAvailableForPurchase
                price {
                    amount
                }
            }
        }
    }
}
"""


@pytest.fixture
def variant_in_two_channels(product_available_in_many_channels):
    return product_available_in_many_channels.variants.get()


def test_marks_listing_as_unavailable_without_touching_prices(
    staff_api_client, variant_in_two_channels, permission_manage_products, channel_USD
):
    # given
    variant = variant_in_two_channels
    listing = variant.channel_listings.get(channel=channel_USD)
    price_amount = listing.price_amount
    cost_price_amount = listing.cost_price_amount
    assert listing.is_available_for_purchase is True

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "input": [
            {
                "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                "isAvailableForPurchase": False,
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_CHANNEL_LISTING_AVAILABILITY_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantChannelListingAvailabilityUpdate"]
    assert data["errors"] == []

    listing.refresh_from_db(
        fields=("is_available_for_purchase", "price_amount", "cost_price_amount")
    )
    assert listing.is_available_for_purchase is False
    assert listing.price_amount == price_amount
    assert listing.cost_price_amount == cost_price_amount


def test_price_survives_a_full_unavailable_available_cycle(
    staff_api_client, variant_in_two_channels, permission_manage_products, channel_USD
):
    """Reproduces the reported bug: the price must not be lost or reset to 0."""
    # given
    variant = variant_in_two_channels
    listing = variant.channel_listings.get(channel=channel_USD)
    listing_pk = listing.pk
    price_amount = listing.price_amount
    cost_price_amount = listing.cost_price_amount

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    for is_available in (False, True):
        response = staff_api_client.post_graphql(
            PRODUCT_VARIANT_CHANNEL_LISTING_AVAILABILITY_UPDATE_MUTATION,
            variables={
                "id": variant_id,
                "input": [
                    {"channelId": channel_id, "isAvailableForPurchase": is_available}
                ],
            },
        )
        content = get_graphql_content(response)
        data = content["data"]["productVariantChannelListingAvailabilityUpdate"]
        assert data["errors"] == []

    # then
    listing = ProductVariantChannelListing.objects.get(
        variant=variant, channel=channel_USD
    )
    assert listing.pk == listing_pk
    assert listing.is_available_for_purchase is True
    assert listing.price_amount == price_amount
    assert listing.cost_price_amount == cost_price_amount


def test_other_channels_are_left_untouched(
    staff_api_client,
    variant_in_two_channels,
    permission_manage_products,
    channel_USD,
    channel_PLN,
):
    # given
    variant = variant_in_two_channels
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "input": [
            {
                "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                "isAvailableForPurchase": False,
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_CHANNEL_LISTING_AVAILABILITY_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantChannelListingAvailabilityUpdate"]
    assert data["errors"] == []

    availability_per_channel = {
        listing["channel"]["slug"]: listing["isAvailableForPurchase"]
        for listing in data["variant"]["channelListings"]
    }
    assert availability_per_channel == {
        channel_USD.slug: False,
        channel_PLN.slug: True,
    }


def test_resolves_the_variant_by_sku(
    staff_api_client, variant_in_two_channels, permission_manage_products, channel_USD
):
    # given
    variant = variant_in_two_channels
    listing = variant.channel_listings.get(channel=channel_USD)
    variables = {
        "sku": variant.sku,
        "input": [
            {
                "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                "isAvailableForPurchase": False,
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_CHANNEL_LISTING_AVAILABILITY_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantChannelListingAvailabilityUpdate"]
    assert data["errors"] == []
    assert data["variant"]["id"] == graphene.Node.to_global_id(
        "ProductVariant", variant.pk
    )

    listing.refresh_from_db(fields=("is_available_for_purchase",))
    assert listing.is_available_for_purchase is False


def test_missing_listing_returns_not_found_and_creates_nothing(
    staff_api_client, variant, permission_manage_products, channel_USD, channel_PLN
):
    # given
    assert variant.channel_listings.filter(channel=channel_PLN).exists() is False
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.pk)
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "input": [
            {
                "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                "isAvailableForPurchase": False,
            },
            {"channelId": channel_pln_id, "isAvailableForPurchase": False},
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_CHANNEL_LISTING_AVAILABILITY_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantChannelListingAvailabilityUpdate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "channelId"
    assert error["code"] == ProductErrorCode.NOT_FOUND.name
    assert error["message"] == ("Variant has no channel listing in the given channels.")
    assert error["channels"] == [channel_pln_id]

    assert variant.channel_listings.filter(channel=channel_PLN).exists() is False
    usd_listing = variant.channel_listings.get(channel=channel_USD)
    assert usd_listing.is_available_for_purchase is True


def test_duplicated_channel_is_rejected(
    staff_api_client, variant, permission_manage_products, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "input": [
            {"channelId": channel_id, "isAvailableForPurchase": False},
            {"channelId": channel_id, "isAvailableForPurchase": True},
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_CHANNEL_LISTING_AVAILABILITY_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantChannelListingAvailabilityUpdate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "channelId"
    assert error["code"] == ProductErrorCode.DUPLICATED_INPUT_ITEM.name
    assert error["message"] == "Duplicated channel ID."
    assert error["channels"] == [channel_id]

    listing = variant.channel_listings.get(channel=channel_USD)
    assert listing.is_available_for_purchase is True


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.graphql.product.mutations.channels.mark_products_in_channels_as_dirty")
def test_unchanged_flag_emits_no_events(
    mocked_mark_dirty,
    mocked_variant_updated,
    staff_api_client,
    variant,
    permission_manage_products,
    channel_USD,
):
    # given
    listing = variant.channel_listings.get(channel=channel_USD)
    assert listing.is_available_for_purchase is True
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "input": [
            {
                "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                "isAvailableForPurchase": True,
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_CHANNEL_LISTING_AVAILABILITY_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantChannelListingAvailabilityUpdate"]
    assert data["errors"] == []
    assert mocked_mark_dirty.call_count == 0
    assert mocked_variant_updated.call_count == 0


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.graphql.product.mutations.channels.mark_products_in_channels_as_dirty")
def test_changed_flag_marks_product_dirty_and_notifies(
    mocked_mark_dirty,
    mocked_variant_updated,
    staff_api_client,
    variant,
    permission_manage_products,
    channel_USD,
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "input": [
            {
                "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                "isAvailableForPurchase": False,
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_CHANNEL_LISTING_AVAILABILITY_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantChannelListingAvailabilityUpdate"]
    assert data["errors"] == []
    mocked_mark_dirty.assert_called_once_with({channel_USD.pk: {variant.product_id}})
    assert mocked_variant_updated.call_count == 1


@pytest.mark.parametrize(
    ("_case", "client_fixture", "permission_fixture", "is_allowed"),
    [
        ("Unauthenticated user should be rejected", "api_client", None, False),
        (
            "Authenticated unprivileged user (non-staff) should be rejected",
            "user_api_client",
            None,
            False,
        ),
        (
            "Authenticated user w/o the permission should be rejected",
            "staff_api_client",
            None,
            False,
        ),
        (
            "Authenticated user w/o the relevant permission should be rejected",
            "staff_api_client",
            "permission_manage_orders",
            False,
        ),
        (
            "Authenticated user w/ the correct permission should be allowed",
            "staff_api_client",
            "permission_manage_products",
            True,
        ),
    ],
)
@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_authorization(
    mocked_variant_updated,
    _case,
    client_fixture,
    permission_fixture,
    is_allowed,
    request,
    variant,
    channel_USD,
):
    # given
    client = request.getfixturevalue(client_fixture)
    if permission_fixture:
        permission = request.getfixturevalue(permission_fixture)
        if client.app:
            client.app.permissions.add(permission)
        elif client.user:
            client.user.user_permissions.add(permission)
        else:
            raise AssertionError("Couldn't add the permission")

    listing = variant.channel_listings.get(channel=channel_USD)
    assert listing.is_available_for_purchase is True

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "input": [
            {
                "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                "isAvailableForPurchase": False,
            }
        ],
    }

    # when
    response = client.post_graphql(
        PRODUCT_VARIANT_CHANNEL_LISTING_AVAILABILITY_UPDATE_MUTATION,
        variables=variables,
    )

    # then
    listing.refresh_from_db(fields=("is_available_for_purchase",))
    if is_allowed:
        content = get_graphql_content(response)
        data = content["data"]["productVariantChannelListingAvailabilityUpdate"]
        assert data["errors"] == []
        assert listing.is_available_for_purchase is False
        assert mocked_variant_updated.call_count == 1
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"]["productVariantChannelListingAvailabilityUpdate"] is None
        assert listing.is_available_for_purchase is True
        assert mocked_variant_updated.call_count == 0


def test_locks_the_listing_rows_before_updating(
    staff_api_client,
    variant,
    permission_manage_products,
    channel_USD,
    capture_queries,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "input": [
            {
                "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                "isAvailableForPurchase": False,
            }
        ],
    }

    # when
    with capture_queries() as ctx:
        response = staff_api_client.post_graphql(
            PRODUCT_VARIANT_CHANNEL_LISTING_AVAILABILITY_UPDATE_MUTATION,
            variables=variables,
        )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantChannelListingAvailabilityUpdate"]
    assert data["errors"] == []

    table = ProductVariantChannelListing._meta.db_table
    listing_queries = [
        query["sql"]
        for query in ctx.captured_queries
        if table in query["sql"]
        and ("FOR UPDATE" in query["sql"] or query["sql"].startswith("UPDATE"))
    ]
    assert len(listing_queries) == 2, listing_queries
    lock_query, update_query = listing_queries
    assert "FOR UPDATE" in lock_query
    assert "ORDER BY" in lock_query
    assert update_query.startswith("UPDATE")


def test_input_longer_than_the_limit_is_rejected(
    staff_api_client, variant, permission_manage_products, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "input": [
            {"channelId": channel_id, "isAvailableForPurchase": False}
            for _ in range(AVAILABILITY_UPDATE_MAX_ITEMS + 1)
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_CHANNEL_LISTING_AVAILABILITY_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantChannelListingAvailabilityUpdate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "input"
    assert error["code"] == ProductErrorCode.INVALID.name
    assert error["message"] == (
        f"Cannot specify more than {AVAILABILITY_UPDATE_MAX_ITEMS} items."
    )

    listing = variant.channel_listings.get(channel=channel_USD)
    assert listing.is_available_for_purchase is True
