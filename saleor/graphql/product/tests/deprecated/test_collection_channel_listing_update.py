import datetime

import graphene
import pytz

from .....product.error_codes import CollectionErrorCode
from ....tests.utils import get_graphql_content

COLLECTION_CHANNEL_LISTING_UPDATE_MUTATION = """
mutation UpdateCollectionChannelListing(
    $id: ID!
    $input: CollectionChannelListingUpdateInput!
) {
    collectionChannelListingUpdate(id: $id, input: $input) {
        errors {
            field
            message
            code
            channels
        }
        collection {
            slug
            channelListings {
                isPublished
                publicationDate
                channel {
                    slug
                }
            }
        }
    }
}
"""


def test_collection_channel_listing_update_as_staff_user(
    staff_api_client,
    published_collection,
    permission_manage_products,
    channel_USD,
    channel_PLN,
):
    # given
    publication_date = datetime.date.today()
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": collection_id,
        "input": {
            "addChannels": [
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
        COLLECTION_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["collectionChannelListingUpdate"]
    collection_data = data["collection"]
    collection_channel_listing = published_collection.channel_listings.get(
        channel=channel_USD
    )
    publication_date_usd = collection_channel_listing.published_at
    assert not data["errors"]
    assert collection_data["slug"] == published_collection.slug
    assert collection_data["channelListings"][0]["isPublished"] is True
    assert (
        collection_data["channelListings"][0]["publicationDate"]
        == publication_date_usd.date().isoformat()
    )
    assert collection_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug

    assert collection_data["channelListings"][1]["isPublished"] is False
    assert (
        collection_data["channelListings"][1]["publicationDate"]
        == publication_date.isoformat()
    )
    assert collection_data["channelListings"][1]["channel"]["slug"] == channel_PLN.slug


def test_collection_channel_listing_update_as_app(
    app_api_client,
    published_collection,
    permission_manage_products,
    channel_USD,
    channel_PLN,
):
    # given
    publication_date = datetime.date.today()
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": collection_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": False,
                    "publicationDate": publication_date,
                }
            ]
        },
    }

    # when
    response = app_api_client.post_graphql(
        COLLECTION_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    collection_channel_listing = published_collection.channel_listings.get(
        channel=channel_USD
    )
    publication_date_usd = collection_channel_listing.published_at
    data = content["data"]["collectionChannelListingUpdate"]
    collection_data = data["collection"]
    assert not data["errors"]
    assert collection_data["slug"] == published_collection.slug
    assert collection_data["channelListings"][0]["isPublished"] is True
    assert (
        collection_data["channelListings"][0]["publicationDate"]
        == publication_date_usd.date().isoformat()
    )
    assert collection_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert collection_data["channelListings"][1]["isPublished"] is False
    assert (
        collection_data["channelListings"][1]["publicationDate"]
        == publication_date.isoformat()
    )
    assert collection_data["channelListings"][1]["channel"]["slug"] == channel_PLN.slug


def test_collection_channel_listing_update_add_channel(
    staff_api_client,
    published_collection,
    permission_manage_products,
    channel_USD,
    channel_PLN,
):
    # given
    publication_date = datetime.date.today()
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": collection_id,
        "input": {
            "addChannels": [
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
        COLLECTION_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    collection_channel_listing = published_collection.channel_listings.get(
        channel=channel_USD
    )
    publication_date_usd = collection_channel_listing.published_at
    data = content["data"]["collectionChannelListingUpdate"]
    collection_data = data["collection"]
    assert not data["errors"]
    assert collection_data["slug"] == published_collection.slug
    assert collection_data["channelListings"][0]["isPublished"] is True
    assert (
        collection_data["channelListings"][0]["publicationDate"]
        == publication_date_usd.date().isoformat()
    )
    assert collection_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert collection_data["channelListings"][1]["isPublished"] is False
    assert (
        collection_data["channelListings"][1]["publicationDate"]
        == publication_date.isoformat()
    )
    assert collection_data["channelListings"][1]["channel"]["slug"] == channel_PLN.slug


def test_collection_channel_listing_update_update_publication_date(
    staff_api_client, collection, permission_manage_products, channel_USD
):
    # given
    publication_date = datetime.date.today()
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": collection_id,
        "input": {
            "addChannels": [
                {"channelId": channel_id, "publicationDate": publication_date}
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        COLLECTION_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["collectionChannelListingUpdate"]
    collection_data = data["collection"]
    assert not data["errors"]
    assert collection_data["slug"] == collection.slug
    assert (
        collection_data["channelListings"][0]["publicationDate"]
        == publication_date.isoformat()
    )
    assert collection_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug


def test_collection_channel_listing_update_update_publication_date_and_published_at(
    staff_api_client, collection, permission_manage_products, channel_USD
):
    """Test that filtering by publication time and date are mutually exclusive."""
    # given
    publication_date = datetime.date.today()
    published_at = datetime.datetime.now(pytz.utc)
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": collection_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "publicationDate": publication_date,
                    "publishedAt": published_at,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        COLLECTION_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["collectionChannelListingUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "publicationDate"
    assert errors[0]["code"] == CollectionErrorCode.INVALID.name
    assert errors[0]["channels"] == [channel_id]
