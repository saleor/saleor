import datetime
from unittest.mock import patch

import graphene
import pytz
from django.utils import timezone
from freezegun import freeze_time

from .....checkout.fetch import fetch_checkout_info
from .....checkout.utils import add_variant_to_checkout
from .....plugins.manager import get_plugins_manager
from .....product.error_codes import ProductErrorCode
from .....product.models import ProductVariant, ProductVariantChannelListing
from .....product.utils.costs import get_product_costs_data
from ....tests.utils import assert_no_permission, get_graphql_content

PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION = """
mutation UpdateProductChannelListing(
    $id: ID!
    $input: ProductChannelListingUpdateInput!
) {
    productChannelListingUpdate(id: $id, input: $input) {
        errors {
            field
            message
            code
            channels
            variants
        }
        product {
            slug
            channelListings {
                isPublished
                publishedAt
                visibleInListings
                channel {
                    slug
                }
                purchaseCost {
                    start {
                        amount
                    }
                    stop {
                        amount
                    }
                }
                margin {
                    start
                    stop
                }
                isAvailableForPurchase
                availableForPurchaseAt
            }
            variants {
                channelListings {
                    channel {
                        slug
                    }
                }
            }
        }
    }
}
"""


def test_product_channel_listing_update_duplicated_ids_in_add_and_remove(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [{"channelId": channel_id, "isPublished": True}],
            "removeChannels": [channel_id],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "input"
    assert errors[0]["code"] == ProductErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["channels"] == [channel_id]


def test_product_channel_listing_update_duplicated_channel_in_add(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {"channelId": channel_id, "isPublished": True},
                {"channelId": channel_id, "isPublished": False},
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "updateChannels"
    assert errors[0]["code"] == ProductErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["channels"] == [channel_id]


def test_product_channel_listing_update_duplicated_channel_in_remove(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {"removeChannels": [channel_id, channel_id]},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "removeChannels"
    assert errors[0]["code"] == ProductErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["channels"] == [channel_id]


def test_product_channel_listing_update_with_empty_input(
    staff_api_client, product, permission_manage_products
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {
        "id": product_id,
        "input": {},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productChannelListingUpdate"]["errors"]
    assert not errors


def test_product_channel_listing_update_with_empty_lists_in_input(
    staff_api_client, product, permission_manage_products
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {
        "id": product_id,
        "input": {"updateChannels": [], "removeChannels": []},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productChannelListingUpdate"]["errors"]
    assert not errors


def test_product_channel_listing_update_as_staff_user(
    staff_api_client, product, permission_manage_products, channel_USD, channel_PLN
):
    # given
    publication_date = datetime.datetime.now(pytz.utc).replace(microsecond=0)
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    available_for_purchase_date = datetime.datetime(2007, 1, 1, tzinfo=pytz.utc)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": False,
                    "publishedAt": publication_date,
                    "visibleInListings": True,
                    "isAvailableForPurchase": True,
                    "availableForPurchaseAt": available_for_purchase_date,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]

    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.filter(channel_id=channel_USD.id)
    purchase_cost, margin = get_product_costs_data(
        variant_channel_listing, True, channel_USD.currency_code
    )
    assert not data["errors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListings"][0]["isPublished"] is True
    assert product_data["channelListings"][0]["publishedAt"] is None
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListings"][0]["visibleInListings"] is True
    assert product_data["channelListings"][0]["isAvailableForPurchase"] is True
    assert (
        datetime.date(1999, 1, 1).isoformat()
        in product_data["channelListings"][0]["availableForPurchaseAt"]
    )
    cost_start = product_data["channelListings"][0]["purchaseCost"]["start"]["amount"]
    cost_stop = product_data["channelListings"][0]["purchaseCost"]["stop"]["amount"]

    assert purchase_cost.start.amount == cost_start
    assert purchase_cost.stop.amount == cost_stop
    assert margin[0] == product_data["channelListings"][0]["margin"]["start"]
    assert margin[1] == product_data["channelListings"][0]["margin"]["stop"]
    assert product_data["channelListings"][1]["isPublished"] is False
    assert (
        product_data["channelListings"][1]["publishedAt"]
        == publication_date.isoformat()
    )
    assert product_data["channelListings"][1]["visibleInListings"] is True
    assert product_data["channelListings"][1]["channel"]["slug"] == channel_PLN.slug
    assert product_data["channelListings"][1]["isAvailableForPurchase"] is True
    assert (
        product_data["channelListings"][1]["availableForPurchaseAt"]
        == available_for_purchase_date.isoformat()
    )


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_product_channel_listing_update_trigger_webhook_product_updated(
    mock_product_updated,
    staff_api_client,
    product,
    permission_manage_products,
    channel_USD,
):
    # given
    publication_date = datetime.datetime.now(pytz.utc)
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    available_for_purchase_date = datetime.datetime(2007, 1, 1, tzinfo=pytz.utc)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": False,
                    "publishedAt": publication_date,
                    "visibleInListings": True,
                    "isAvailableForPurchase": True,
                    "availableForPurchaseAt": available_for_purchase_date,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    get_graphql_content(response)

    # then
    mock_product_updated.assert_called_once_with(product)
    listings = mock_product_updated.call_args.args[0].channel_listings.all()
    for listing in listings:
        if listing.channel == channel_USD:
            assert listing.available_for_purchase_at == available_for_purchase_date


def test_product_channel_listing_update_as_app(
    app_api_client, product, permission_manage_products, channel_USD, channel_PLN
):
    # given
    publication_date = datetime.datetime.now(pytz.utc).replace(microsecond=0)
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    available_for_purchase_date = datetime.datetime(2007, 1, 1, tzinfo=pytz.utc)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": False,
                    "publishedAt": publication_date,
                    "visibleInListings": True,
                    "isAvailableForPurchase": True,
                    "availableForPurchaseAt": available_for_purchase_date,
                }
            ]
        },
    }

    # when
    response = app_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]
    assert not data["errors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListings"][0]["isPublished"] is True
    assert product_data["channelListings"][0]["publishedAt"] is None
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListings"][0]["visibleInListings"] is True
    assert product_data["channelListings"][0]["isAvailableForPurchase"] is True
    assert (
        datetime.date(1999, 1, 1).isoformat()
        in product_data["channelListings"][0]["availableForPurchaseAt"]
    )
    assert product_data["channelListings"][1]["isPublished"] is False
    assert (
        product_data["channelListings"][1]["publishedAt"]
        == publication_date.isoformat()
    )
    assert product_data["channelListings"][1]["visibleInListings"] is True
    assert product_data["channelListings"][1]["channel"]["slug"] == channel_PLN.slug
    assert product_data["channelListings"][1]["isAvailableForPurchase"] is True
    assert (
        product_data["channelListings"][1]["availableForPurchaseAt"]
        == available_for_purchase_date.isoformat()
    )


def test_product_channel_listing_update_as_customer(
    user_api_client, product, channel_PLN
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": product_id,
        "input": {"updateChannels": [{"channelId": channel_id, "isPublished": False}]},
    }

    # when
    response = user_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION, variables=variables
    )

    # then
    assert_no_permission(response)


def test_product_channel_listing_update_as_anonymous(api_client, product, channel_PLN):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": product_id,
        "input": {"updateChannels": [{"channelId": channel_id, "isPublished": False}]},
    }

    # when
    response = api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION, variables=variables
    )

    # then
    assert_no_permission(response)


def test_product_channel_listing_update_add_channel(
    staff_api_client, product, permission_manage_products, channel_USD, channel_PLN
):
    # given
    publication_date = datetime.datetime.now(pytz.utc).replace(microsecond=0)
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    available_for_purchase_date = datetime.datetime(2007, 1, 1, tzinfo=pytz.utc)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": False,
                    "publishedAt": publication_date,
                    "visibleInListings": True,
                    "isAvailableForPurchase": True,
                    "availableForPurchaseAt": available_for_purchase_date,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]
    assert not data["errors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListings"][0]["isPublished"] is True
    assert product_data["channelListings"][0]["publishedAt"] is None
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListings"][1]["isPublished"] is False
    assert (
        product_data["channelListings"][1]["publishedAt"]
        == publication_date.isoformat()
    )
    assert product_data["channelListings"][1]["channel"]["slug"] == channel_PLN.slug
    assert product_data["channelListings"][1]["visibleInListings"] is True
    assert product_data["channelListings"][1]["isAvailableForPurchase"] is True
    assert (
        product_data["channelListings"][1]["availableForPurchaseAt"]
        == available_for_purchase_date.isoformat()
    )


@freeze_time("2020-03-18 12:00:00")
def test_product_channel_listing_update_add_channel_without_publication_date(
    staff_api_client, product, permission_manage_products, channel_USD, channel_PLN
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": product_id,
        "input": {"updateChannels": [{"channelId": channel_id, "isPublished": True}]},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]
    assert not data["errors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListings"][0]["isPublished"] is True
    assert product_data["channelListings"][0]["publishedAt"] is None
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListings"][1]["isPublished"] is True
    assert (
        datetime.date(2020, 3, 18).isoformat()
        in product_data["channelListings"][1]["publishedAt"]
    )
    assert product_data["channelListings"][1]["channel"]["slug"] == channel_PLN.slug


def test_product_channel_listing_update_unpublished(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product.channel_listings.update(published_at=timezone.now())
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {"updateChannels": [{"channelId": channel_id, "isPublished": False}]},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]
    assert not data["errors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListings"][0]["isPublished"] is False
    assert (
        datetime.date.today().isoformat()
        in product_data["channelListings"][0]["publishedAt"]
    )
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListings"][0]["visibleInListings"] is True
    assert product_data["channelListings"][0]["isAvailableForPurchase"] is True
    assert (
        datetime.date(1999, 1, 1).isoformat()
        in product_data["channelListings"][0]["availableForPurchaseAt"]
    )


@freeze_time("2020-03-18 12:00:00")
def test_product_channel_listing_update_publish_without_publication_date(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product.channel_listings.update(is_published=False)
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {"updateChannels": [{"channelId": channel_id, "isPublished": True}]},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]
    assert not data["errors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListings"][0]["isPublished"] is True
    assert (
        datetime.date(2020, 3, 18).isoformat()
        in product_data["channelListings"][0]["publishedAt"]
    )
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug


def test_product_channel_listing_update_remove_publication_date(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product.channel_listings.update(published_at=timezone.now())
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {"updateChannels": [{"channelId": channel_id, "publishedAt": None}]},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]
    assert not data["errors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListings"][0]["isPublished"] is True
    assert product_data["channelListings"][0]["publishedAt"] is None
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListings"][0]["visibleInListings"] is True
    assert product_data["channelListings"][0]["isAvailableForPurchase"] is True
    assert (
        datetime.date(1999, 1, 1).isoformat()
        in product_data["channelListings"][0]["availableForPurchaseAt"]
    )


def test_product_channel_listing_update_visible_in_listings(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [{"channelId": channel_id, "visibleInListings": False}]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]
    assert not data["errors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListings"][0]["isPublished"] is True
    assert product_data["channelListings"][0]["publishedAt"] is None
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListings"][0]["visibleInListings"] is False
    assert product_data["channelListings"][0]["isAvailableForPurchase"] is True
    assert (
        datetime.date(1999, 1, 1).isoformat()
        in product_data["channelListings"][0]["availableForPurchaseAt"]
    )


def test_product_channel_listing_update_update_publication_data(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    publication_date = datetime.datetime.now(pytz.utc).replace(microsecond=0)
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": False,
                    "publishedAt": publication_date,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]
    assert not data["errors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListings"][0]["isPublished"] is False
    assert (
        product_data["channelListings"][0]["publishedAt"]
        == publication_date.isoformat()
    )
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListings"][0]["visibleInListings"] is True
    assert product_data["channelListings"][0]["isAvailableForPurchase"] is True
    assert (
        datetime.date(1999, 1, 1).isoformat()
        in product_data["channelListings"][0]["availableForPurchaseAt"]
    )


def test_product_channel_listing_update_update_is_available_for_purchase_false(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {"channelId": channel_id, "isAvailableForPurchase": False}
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]
    assert not data["errors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListings"][0]["isPublished"] is True
    assert not product_data["channelListings"][0]["publishedAt"]
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListings"][0]["visibleInListings"] is True
    assert product_data["channelListings"][0]["isAvailableForPurchase"] is False
    assert not product_data["channelListings"][0]["availableForPurchaseAt"]


def test_product_channel_listing_update_update_is_available_for_purchase_without_date(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {"channelId": channel_id, "isAvailableForPurchase": True}
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]
    assert not data["errors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListings"][0]["isPublished"] is True
    assert not product_data["channelListings"][0]["publishedAt"]
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListings"][0]["visibleInListings"] is True
    assert product_data["channelListings"][0]["isAvailableForPurchase"] is True
    assert (
        datetime.date.today().isoformat()
        in product_data["channelListings"][0]["availableForPurchaseAt"]
    )


def test_product_channel_listing_update_update_is_available_for_purchase_past_date(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    available_for_purchase_date = datetime.datetime(2007, 1, 1, tzinfo=pytz.utc)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isAvailableForPurchase": True,
                    "availableForPurchaseAt": available_for_purchase_date,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]
    assert not data["errors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListings"][0]["isPublished"] is True
    assert not product_data["channelListings"][0]["publishedAt"]
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListings"][0]["visibleInListings"] is True
    assert product_data["channelListings"][0]["isAvailableForPurchase"] is True
    assert (
        product_data["channelListings"][0]["availableForPurchaseAt"]
        == available_for_purchase_date.isoformat()
    )


def test_product_channel_listing_update_update_is_available_for_purchase_future_date(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    available_for_purchase_date = datetime.datetime.now(pytz.utc).replace(
        microsecond=0
    ) + datetime.timedelta(days=1)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isAvailableForPurchase": True,
                    "availableForPurchaseAt": available_for_purchase_date,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]
    assert not data["errors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListings"][0]["isPublished"] is True
    assert not product_data["channelListings"][0]["publishedAt"]
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListings"][0]["visibleInListings"] is True
    assert product_data["channelListings"][0]["isAvailableForPurchase"] is False
    assert (
        product_data["channelListings"][0]["availableForPurchaseAt"]
        == available_for_purchase_date.isoformat()
    )


def test_product_channel_listing_update_update_is_available_for_purchase_false_and_date(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    available_for_purchase_date = datetime.datetime.now(pytz.utc) + datetime.timedelta(
        days=1
    )
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isAvailableForPurchase": False,
                    "availableForPurchaseAt": available_for_purchase_date,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    errors = data["errors"]
    assert errors[0]["field"] == "availableForPurchaseDate"
    assert errors[0]["code"] == ProductErrorCode.INVALID.name
    assert errors[0]["channels"] == [channel_id]
    assert len(errors) == 1


def test_product_channel_listing_update_remove_channel(
    staff_api_client,
    product_available_in_many_channels,
    permission_manage_products,
    channel_USD,
    channel_PLN,
):
    # given
    product = product_available_in_many_channels
    product_channel_listing_pln = product.channel_listings.get(channel=channel_PLN)
    variant = product.variants.get()
    variant_channel_listing_pln = variant.channel_listings.get(channel=channel_PLN)
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {"removeChannels": [channel_id]},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]
    assert not data["errors"]
    assert product_data["slug"] == product.slug
    assert len(product_data["channelListings"]) == 1
    assert product.channel_listings.get() == product_channel_listing_pln
    assert variant.channel_listings.get() == variant_channel_listing_pln


def test_product_channel_listing_update_remove_channel_removes_checkout_lines(
    staff_api_client,
    product_available_in_many_channels,
    permission_manage_products,
    checkout,
    channel_USD,
    channel_PLN,
):
    # given
    product = product_available_in_many_channels
    variant = product.variants.get()
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 1)

    assert checkout.lines.all().exists()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {"removeChannels": [channel_id]},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    assert not data["errors"]
    assert not checkout.lines.all().exists()


def test_product_channel_listing_update_remove_not_assigned_channel(
    staff_api_client, product, permission_manage_products, channel_USD, channel_PLN
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": product_id,
        "input": {"removeChannels": [channel_id]},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]
    assert not data["errors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListings"][0]["isPublished"] is True
    assert product_data["channelListings"][0]["publishedAt"] is None
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug


def test_product_channel_listing_update_publish_product_without_category(
    staff_api_client, product, permission_manage_products, channel_USD, channel_PLN
):
    # given
    product.channel_listings.all().delete()
    product.category = None
    product.save()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_usd_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {"channelId": channel_usd_id, "isPublished": True},
                {"channelId": channel_pln_id, "isPublished": False},
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    errors = data["errors"]
    assert errors[0]["field"] == "isPublished"
    assert errors[0]["code"] == ProductErrorCode.PRODUCT_WITHOUT_CATEGORY.name
    assert errors[0]["channels"] == [channel_usd_id]
    assert len(errors) == 1


def test_product_channel_listing_update_available_for_purchase_product_without_category(
    staff_api_client, product, permission_manage_products, channel_USD, channel_PLN
):
    # given
    product.channel_listings.all().delete()
    product.category = None
    product.save()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_usd_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {"channelId": channel_usd_id, "isAvailableForPurchase": True},
                {"channelId": channel_pln_id, "isAvailableForPurchase": False},
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    errors = data["errors"]
    assert errors[0]["field"] == "isPublished"
    assert errors[0]["code"] == ProductErrorCode.PRODUCT_WITHOUT_CATEGORY.name
    assert errors[0]["channels"] == [channel_usd_id]
    assert len(errors) == 1


def test_product_channel_listing_add_variant_as_staff_user(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product.variants.all().delete()
    variant_1 = ProductVariant.objects.create(product=product, sku="321")
    variant_2 = ProductVariant.objects.create(product=product, sku="333")
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.pk)
    variant_2_id = graphene.Node.to_global_id("ProductVariant", variant_2.pk)
    variants = [variant_1_id, variant_2_id]

    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [{"channelId": channel_id, "addVariants": variants}]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    variant_data = data["product"]["variants"]

    assert not data["errors"]
    assert variant_data[0]["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert variant_data[1]["channelListings"][0]["channel"]["slug"] == channel_USD.slug


def test_product_channel_listing_add_variant_as_app(
    app_api_client, product, permission_manage_products, channel_USD
):
    # given
    product.variants.all().delete()
    variant_1 = ProductVariant.objects.create(product=product, sku="321")
    variant_2 = ProductVariant.objects.create(product=product, sku="333")
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.pk)
    variant_2_id = graphene.Node.to_global_id("ProductVariant", variant_2.pk)
    variants = [variant_1_id, variant_2_id]

    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [{"channelId": channel_id, "addVariants": variants}]
        },
    }

    # when
    response = app_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    variant_data = data["product"]["variants"]

    assert not data["errors"]
    assert variant_data[0]["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert variant_data[1]["channelListings"][0]["channel"]["slug"] == channel_USD.slug


def test_product_channel_listing_remove_variant_as_staff_user(
    staff_api_client, product, permission_manage_products, channel_USD, channel_PLN
):
    # given
    variant = product.variants.first()
    ProductVariantChannelListing.objects.create(channel=channel_PLN, variant=variant)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {"channelId": channel_id, "removeVariants": [variant_id]}
            ]
        },
    }

    assert len(variant.channel_listings.all()) == 2
    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    assert not data["errors"]

    assert len(variant.channel_listings.all()) == 1


def test_product_channel_listing_remove_variant_as_app(
    app_api_client, product, permission_manage_products, channel_USD, channel_PLN
):
    # given
    variant = product.variants.first()
    ProductVariantChannelListing.objects.create(channel=channel_PLN, variant=variant)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {"channelId": channel_id, "removeVariants": [variant_id]}
            ]
        },
    }

    assert len(variant.channel_listings.all()) == 2
    # when
    response = app_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    assert not data["errors"]

    assert len(variant.channel_listings.all()) == 1


def test_product_channel_listing_remove_variant_removes_checkout_lines(
    staff_api_client,
    product,
    permission_manage_products,
    checkout,
    channel_USD,
    channel_PLN,
):
    # given
    variant = product.variants.first()
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 1)

    assert checkout.lines.all().exists()

    ProductVariantChannelListing.objects.create(channel=channel_PLN, variant=variant)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {"channelId": channel_id, "removeVariants": [variant_id]}
            ]
        },
    }

    assert len(variant.channel_listings.all()) == 2
    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    assert not data["errors"]

    assert len(variant.channel_listings.all()) == 1

    assert not checkout.lines.all().exists()


def test_product_channel_listing_add_variant_duplicated_ids_in_add_and_remove(
    staff_api_client, product, permission_manage_products, channel_USD, channel_PLN
):
    # given
    variant = product.variants.first()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variants = [variant_id]
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": True,
                    "addVariants": variants,
                    "removeVariants": variants,
                }
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "addVariants"
    assert errors[0]["code"] == ProductErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["variants"] == variants


def test_product_channel_listing_add_variant_with_existing_channel_listing(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    variant = product.variants.first()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variants = [variant_id]
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": True,
                    "addVariants": variants,
                }
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "addVariants"
    assert errors[0]["code"] == ProductErrorCode.ALREADY_EXISTS.name


def test_product_channel_listing_remove_last_variant_channel_listing(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    assert product.channel_listings.filter(channel=channel_USD).exists()
    variant = product.variants.first()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variants = [variant_id]
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": True,
                    "removeVariants": variants,
                }
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    assert not data["errors"]
    assert not product.channel_listings.filter(channel=channel_USD).exists()
