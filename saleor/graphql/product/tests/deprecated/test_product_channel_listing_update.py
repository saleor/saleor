import datetime
from unittest.mock import patch

import graphene
import pytz

from .....product.error_codes import ProductErrorCode
from .....product.utils.costs import get_product_costs_data
from ....tests.utils import get_graphql_content

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
                publicationDate
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
                availableForPurchase
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


def test_product_channel_listing_update_as_staff_user(
    staff_api_client, product, permission_manage_products, channel_USD, channel_PLN
):
    # given
    publication_date = datetime.date.today()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    available_for_purchase_date = datetime.date(2007, 1, 1)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": False,
                    "publicationDate": publication_date,
                    "visibleInListings": True,
                    "isAvailableForPurchase": True,
                    "availableForPurchaseDate": available_for_purchase_date,
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
    assert product_data["channelListings"][0]["publicationDate"] is None
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListings"][0]["visibleInListings"] is True
    assert product_data["channelListings"][0]["isAvailableForPurchase"] is True
    assert (
        product_data["channelListings"][0]["availableForPurchase"]
        == datetime.date(1999, 1, 1).isoformat()
    )
    cost_start = product_data["channelListings"][0]["purchaseCost"]["start"]["amount"]
    cost_stop = product_data["channelListings"][0]["purchaseCost"]["stop"]["amount"]

    assert purchase_cost.start.amount == cost_start
    assert purchase_cost.stop.amount == cost_stop
    assert margin[0] == product_data["channelListings"][0]["margin"]["start"]
    assert margin[1] == product_data["channelListings"][0]["margin"]["stop"]
    assert product_data["channelListings"][1]["isPublished"] is False
    assert (
        product_data["channelListings"][1]["publicationDate"]
        == publication_date.isoformat()
    )
    assert product_data["channelListings"][1]["visibleInListings"] is True
    assert product_data["channelListings"][1]["channel"]["slug"] == channel_PLN.slug
    assert product_data["channelListings"][1]["isAvailableForPurchase"] is True
    assert (
        product_data["channelListings"][1]["availableForPurchase"]
        == available_for_purchase_date.isoformat()
    )


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_product_channel_listing_update_trigger_webhook_product_updated(
    mock_product_updated,
    staff_api_client,
    product,
    permission_manage_products,
    channel_USD,
    channel_PLN,
):
    # given
    publication_date = datetime.date.today()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    available_for_purchase_date = datetime.date(2007, 1, 1)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": False,
                    "publicationDate": publication_date,
                    "visibleInListings": True,
                    "isAvailableForPurchase": True,
                    "availableForPurchaseDate": available_for_purchase_date,
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


def test_product_channel_listing_update_add_channel(
    staff_api_client, product, permission_manage_products, channel_USD, channel_PLN
):
    # given
    publication_date = datetime.date.today()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    available_for_purchase_date = datetime.date(2007, 1, 1)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": False,
                    "publicationDate": publication_date,
                    "visibleInListings": True,
                    "isAvailableForPurchase": True,
                    "availableForPurchaseDate": available_for_purchase_date,
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
    assert product_data["channelListings"][0]["publicationDate"] is None
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListings"][1]["isPublished"] is False
    assert (
        product_data["channelListings"][1]["publicationDate"]
        == publication_date.isoformat()
    )
    assert product_data["channelListings"][1]["channel"]["slug"] == channel_PLN.slug
    assert product_data["channelListings"][1]["visibleInListings"] is True
    assert product_data["channelListings"][1]["isAvailableForPurchase"] is True
    assert (
        product_data["channelListings"][1]["availableForPurchase"]
        == available_for_purchase_date.isoformat()
    )


def test_product_channel_listing_update_update_publication_data(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    publication_date = datetime.date.today()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": False,
                    "publicationDate": publication_date,
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
        product_data["channelListings"][0]["publicationDate"]
        == publication_date.isoformat()
    )
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListings"][0]["visibleInListings"] is True
    assert product_data["channelListings"][0]["isAvailableForPurchase"] is True
    assert (
        product_data["channelListings"][0]["availableForPurchase"]
        == datetime.date(1999, 1, 1).isoformat()
    )


def test_product_channel_listing_update_update_publication_date_and_published_at(
    staff_api_client, product, permission_manage_products, channel_USD
):
    """Ensure an error is raised when both publicationDate and publishedAt date
    is given."""
    # given
    publication_date = datetime.date.today()
    published_at = datetime.datetime.now(pytz.utc)
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": False,
                    "publicationDate": publication_date,
                    "publishedAt": published_at,
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

    # then
    content = get_graphql_content(response)
    data = content["data"]["productChannelListingUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "publicationDate"
    assert errors[0]["code"] == ProductErrorCode.INVALID.name
    assert errors[0]["channels"] == [channel_id]


def test_product_channel_listing_update_update_is_available_for_purchase_past_date(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    available_for_purchase_date = datetime.date(2007, 1, 1)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isAvailableForPurchase": True,
                    "availableForPurchaseDate": available_for_purchase_date,
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
    assert not product_data["channelListings"][0]["publicationDate"]
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListings"][0]["visibleInListings"] is True
    assert product_data["channelListings"][0]["isAvailableForPurchase"] is True
    assert (
        product_data["channelListings"][0]["availableForPurchase"]
        == available_for_purchase_date.isoformat()
    )


def test_product_channel_listing_update_update_is_available_for_purchase_future_date(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    available_for_purchase_date = datetime.date.today() + datetime.timedelta(days=1)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isAvailableForPurchase": True,
                    "availableForPurchaseDate": available_for_purchase_date,
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
    assert not product_data["channelListings"][0]["publicationDate"]
    assert product_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListings"][0]["visibleInListings"] is True
    assert product_data["channelListings"][0]["isAvailableForPurchase"] is False
    assert (
        product_data["channelListings"][0]["availableForPurchase"]
        == available_for_purchase_date.isoformat()
    )


def test_product_channel_listing_update_update_is_available_for_purchase_false_and_date(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    available_for_purchase_date = datetime.date.today() + datetime.timedelta(days=1)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isAvailableForPurchase": False,
                    "availableForPurchaseDate": available_for_purchase_date,
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


def test_product_channel_listing_update_available_for_purchase_both_date_value_given(
    staff_api_client, product, permission_manage_products, channel_USD
):
    """Ensure an error is raised when both availableForPurchaseDate and
    availableForPurchaseAt date is given."""
    # given
    available_for_purchase_date = datetime.date.today()
    available_for_purchase_at = datetime.datetime.now(pytz.utc)
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {
            "updateChannels": [
                {
                    "channelId": channel_id,
                    "isAvailableForPurchase": True,
                    "availableForPurchaseDate": available_for_purchase_date,
                    "availableForPurchaseAt": available_for_purchase_at,
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

    # then
    content = get_graphql_content(response)
    data = content["data"]["productChannelListingUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "availableForPurchaseDate"
    assert errors[0]["code"] == ProductErrorCode.INVALID.name
    assert errors[0]["channels"] == [channel_id]
