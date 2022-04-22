import datetime

import graphene
import pytz
from freezegun import freeze_time

from ....product.error_codes import CollectionErrorCode
from ...tests.utils import assert_no_permission, get_graphql_content

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
                publishedAt
                channel {
                    slug
                }
            }
        }
    }
}
"""


def test_collection_channel_listing_update_duplicated_ids_in_add_and_remove(
    staff_api_client, collection, permission_manage_products, channel_USD
):
    # given
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": collection_id,
        "input": {
            "addChannels": [{"channelId": channel_id, "isPublished": True}],
            "removeChannels": [channel_id],
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
    errors = content["data"]["collectionChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "input"
    assert errors[0]["code"] == CollectionErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["channels"] == [channel_id]


def test_collection_channel_listing_update_duplicated_channel_in_add(
    staff_api_client, collection, permission_manage_products, channel_USD
):
    # given
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": collection_id,
        "input": {
            "addChannels": [
                {"channelId": channel_id, "isPublished": True},
                {"channelId": channel_id, "isPublished": False},
            ],
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
    errors = content["data"]["collectionChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "addChannels"
    assert errors[0]["code"] == CollectionErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["channels"] == [channel_id]


def test_collection_channel_listing_update_duplicated_channel_in_remove(
    staff_api_client, collection, permission_manage_products, channel_USD
):
    # given
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": collection_id,
        "input": {"removeChannels": [channel_id, channel_id]},
    }

    # when
    response = staff_api_client.post_graphql(
        COLLECTION_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["collectionChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "removeChannels"
    assert errors[0]["code"] == CollectionErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["channels"] == [channel_id]


def test_collection_channel_listing_update_with_empty_input(
    staff_api_client, collection, permission_manage_products
):
    # given
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    variables = {
        "id": collection_id,
        "input": {},
    }

    # when
    response = staff_api_client.post_graphql(
        COLLECTION_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["collectionChannelListingUpdate"]["errors"]
    assert not errors


def test_collection_channel_listing_update_with_empty_lists_in_input(
    staff_api_client, collection, permission_manage_products
):
    # given
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    variables = {
        "id": collection_id,
        "input": {"addChannels": [], "removeChannels": []},
    }

    # when
    response = staff_api_client.post_graphql(
        COLLECTION_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["collectionChannelListingUpdate"]["errors"]
    assert not errors


def test_collection_channel_listing_update_as_staff_user(
    staff_api_client,
    published_collection,
    permission_manage_products,
    channel_USD,
    channel_PLN,
):
    # given
    publication_date = datetime.datetime.now(pytz.utc).replace(microsecond=0)
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": collection_id,
        "input": {
            "addChannels": [
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
        collection_data["channelListings"][0]["publishedAt"]
        == publication_date_usd.isoformat()
    )
    assert collection_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug

    assert collection_data["channelListings"][1]["isPublished"] is False
    assert (
        collection_data["channelListings"][1]["publishedAt"]
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
    publication_date = datetime.datetime.now(pytz.utc).replace(microsecond=0)
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": collection_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": False,
                    "publishedAt": publication_date,
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
        collection_data["channelListings"][0]["publishedAt"]
        == publication_date_usd.isoformat()
    )
    assert collection_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert collection_data["channelListings"][1]["isPublished"] is False
    assert (
        collection_data["channelListings"][1]["publishedAt"]
        == publication_date.isoformat()
    )
    assert collection_data["channelListings"][1]["channel"]["slug"] == channel_PLN.slug


def test_collection_channel_listing_update_as_customer(
    user_api_client, collection, channel_PLN
):
    # given
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": collection_id,
        "input": {"addChannels": [{"channelId": channel_id, "isPublished": False}]},
    }

    # when
    response = user_api_client.post_graphql(
        COLLECTION_CHANNEL_LISTING_UPDATE_MUTATION, variables=variables
    )

    # then
    assert_no_permission(response)


def test_collection_channel_listing_update_as_anonymous(
    api_client, collection, channel_PLN
):
    # given
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": collection_id,
        "input": {"addChannels": [{"channelId": channel_id, "isPublished": False}]},
    }

    # when
    response = api_client.post_graphql(
        COLLECTION_CHANNEL_LISTING_UPDATE_MUTATION, variables=variables
    )

    # then
    assert_no_permission(response)


def test_collection_channel_listing_update_add_channel(
    staff_api_client,
    published_collection,
    permission_manage_products,
    channel_USD,
    channel_PLN,
):
    # given
    publication_date = datetime.datetime.now(pytz.utc).replace(microsecond=0)
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": collection_id,
        "input": {
            "addChannels": [
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
        collection_data["channelListings"][0]["publishedAt"]
        == publication_date_usd.isoformat()
    )
    assert collection_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert collection_data["channelListings"][1]["isPublished"] is False
    assert (
        collection_data["channelListings"][1]["publishedAt"]
        == publication_date.isoformat()
    )
    assert collection_data["channelListings"][1]["channel"]["slug"] == channel_PLN.slug


def test_collection_channel_listing_update_unpublished(
    staff_api_client, published_collection, permission_manage_products, channel_USD
):
    # given
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": collection_id,
        "input": {"addChannels": [{"channelId": channel_id, "isPublished": False}]},
    }

    # when
    response = staff_api_client.post_graphql(
        COLLECTION_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)
    collection_channel_listing = published_collection.channel_listings.get()
    publication_date_usd = collection_channel_listing.published_at

    # then
    data = content["data"]["collectionChannelListingUpdate"]
    collection_data = data["collection"]
    assert not data["errors"]
    assert collection_data["slug"] == published_collection.slug
    assert collection_data["channelListings"][0]["isPublished"] is False
    assert (
        collection_data["channelListings"][0]["publishedAt"]
        == publication_date_usd.isoformat()
    )
    assert collection_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug


def test_collection_channel_listing_update_update_publication_date(
    staff_api_client, collection, permission_manage_products, channel_USD
):
    # given
    publication_date = datetime.datetime.now(pytz.utc).replace(microsecond=0)
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": collection_id,
        "input": {
            "addChannels": [{"channelId": channel_id, "publishedAt": publication_date}]
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
        collection_data["channelListings"][0]["publishedAt"]
        == publication_date.isoformat()
    )
    assert collection_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug


def test_collection_channel_listing_update_remove_not_assigned_channel(
    staff_api_client,
    published_collection,
    permission_manage_products,
    channel_USD,
    channel_PLN,
):
    # given
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": collection_id,
        "input": {"removeChannels": [channel_id]},
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
    publication_date = collection_channel_listing.published_at
    data = content["data"]["collectionChannelListingUpdate"]
    collection_data = data["collection"]
    assert not data["errors"]
    assert collection_data["slug"] == published_collection.slug
    assert collection_data["channelListings"][0]["isPublished"] is True
    assert (
        collection_data["channelListings"][0]["publishedAt"]
        == publication_date.isoformat()
    )
    assert collection_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug


@freeze_time("2020-03-18 12:00:00")
def test_collection_channel_listing_update_add_channel_without_publication_date(
    staff_api_client,
    published_collection,
    permission_manage_products,
    channel_USD,
    channel_PLN,
):
    # given
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": collection_id,
        "input": {"addChannels": [{"channelId": channel_id, "isPublished": True}]},
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
    assert collection_data["slug"] == published_collection.slug
    assert collection_data["channelListings"][0]["isPublished"] is True
    assert collection_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
    assert collection_data["channelListings"][1]["isPublished"] is True
    assert (
        collection_data["channelListings"][1]["publishedAt"]
        == datetime.datetime.now(pytz.utc).isoformat()
    )
    assert collection_data["channelListings"][1]["channel"]["slug"] == channel_PLN.slug


@freeze_time("2020-03-18 12:00:00")
def test_collection_channel_listing_update_publish_without_publication_date(
    staff_api_client, published_collection, permission_manage_products, channel_USD
):
    # given
    published_collection.channel_listings.update(is_published=False)
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": collection_id,
        "input": {"addChannels": [{"channelId": channel_id, "isPublished": True}]},
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
    assert collection_data["slug"] == published_collection.slug
    assert collection_data["channelListings"][0]["isPublished"] is True
    assert (
        collection_data["channelListings"][0]["publishedAt"]
        == datetime.datetime.now(pytz.utc).isoformat()
    )
    assert collection_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug
