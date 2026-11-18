import datetime

import graphene
import pytest
from freezegun import freeze_time

from .....product.error_codes import CollectionErrorCode, ProductErrorCode
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

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
    publication_date = datetime.datetime.now(tz=datetime.UTC).replace(microsecond=0)
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
    publication_date = datetime.datetime.now(tz=datetime.UTC).replace(microsecond=0)
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
    publication_date = datetime.datetime.now(tz=datetime.UTC).replace(microsecond=0)
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
    publication_date = datetime.datetime.now(tz=datetime.UTC).replace(microsecond=0)
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
        == datetime.datetime.now(tz=datetime.UTC).isoformat()
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
        == datetime.datetime.now(tz=datetime.UTC).isoformat()
    )
    assert collection_data["channelListings"][0]["channel"]["slug"] == channel_USD.slug


COLLECTION_CHANNEL_LISTING_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION = """
mutation UpdateCollectionChannelListing(
    $id: ID
    $externalReference: String
    $input: CollectionChannelListingUpdateInput!
) {
    collectionChannelListingUpdate(
        id: $id, externalReference: $externalReference, input: $input
    ) {
        errors {
            field
            message
            code
        }
        collection {
            id
            channelListings {
                isPublished
                channel {
                    slug
                }
            }
        }
    }
}
"""


def test_by_external_reference(
    staff_api_client, published_collection, permission_manage_products, channel_USD
):
    # given
    collection = published_collection
    external_reference = "collection-ext-ref"
    collection.external_reference = external_reference
    collection.save(update_fields=["external_reference"])
    listing = collection.channel_listings.get(channel=channel_USD)
    assert listing.is_published is True
    variables = {
        "externalReference": external_reference,
        "input": {
            "addChannels": [
                {
                    "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                    "isPublished": False,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        COLLECTION_CHANNEL_LISTING_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["collectionChannelListingUpdate"]
    assert data["errors"] == []
    assert data["collection"] == {
        "id": graphene.Node.to_global_id("Collection", collection.pk),
        "channelListings": [
            {"isPublished": False, "channel": {"slug": channel_USD.slug}}
        ],
    }
    listing.refresh_from_db(fields=("is_published",))
    assert listing.is_published is False


@pytest.mark.parametrize(
    ("_case", "identifiers", "error_field", "error_code", "message"),
    [
        (
            "omitted",
            {},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'externalReference'.",
        ),
        (
            "null",
            {"id": None, "externalReference": None},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'externalReference'.",
        ),
        (
            "empty",
            {"externalReference": ""},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'externalReference'.",
        ),
        (
            "both",
            {"externalReference": "existing-reference"},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "Argument 'id' cannot be combined with 'externalReference'",
        ),
        (
            "not_found",
            {"externalReference": "missing-reference"},
            "externalReference",
            ProductErrorCode.NOT_FOUND,
            "Couldn't resolve to a node: missing-reference",
        ),
    ],
)
def test_external_reference_invalid_identifiers(
    _case,
    identifiers,
    error_field,
    error_code,
    message,
    staff_api_client,
    published_collection,
    permission_manage_products,
    channel_USD,
):
    # given
    collection = published_collection
    collection.external_reference = "existing-reference"
    collection.save(update_fields=["external_reference"])
    listing = collection.channel_listings.get(channel=channel_USD)
    assert listing.is_published is True
    variables = dict(identifiers)
    if _case == "both":
        variables["id"] = graphene.Node.to_global_id("Collection", collection.pk)
    variables["input"] = {
        "addChannels": [
            {
                "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                "isPublished": False,
            }
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        COLLECTION_CHANNEL_LISTING_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    data = get_graphql_content(response)["data"]["collectionChannelListingUpdate"]
    assert data["collection"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    listing.refresh_from_db(fields=("is_published",))
    assert listing.is_published is True


@pytest.mark.parametrize(
    ("_case", "client_fixture", "is_allowed"),
    [
        ("anonymous", "api_client", False),
        ("customer", "user_api_client", False),
        ("staff_without_permission", "staff_api_client", False),
        ("staff_with_permission", "staff_api_client", True),
        ("app_without_permission", "app_api_client", False),
        ("app_with_permission", "app_api_client", True),
    ],
)
def test_external_reference_authorization(
    _case,
    client_fixture,
    is_allowed,
    request,
    published_collection,
    permission_manage_products,
    channel_USD,
):
    # given
    client = request.getfixturevalue(client_fixture)
    collection = published_collection
    external_reference = "existing-reference"
    collection.external_reference = external_reference
    collection.save(update_fields=["external_reference"])
    listing = collection.channel_listings.get(channel=channel_USD)
    assert listing.is_published is True
    variables = {
        "externalReference": external_reference,
        "input": {
            "addChannels": [
                {
                    "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                    "isPublished": False,
                }
            ]
        },
    }

    # when
    response = client.post_graphql(
        COLLECTION_CHANNEL_LISTING_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    listing.refresh_from_db(fields=("is_published",))
    if is_allowed:
        data = get_graphql_content(response)["data"]["collectionChannelListingUpdate"]
        assert data["errors"] == []
        assert data["collection"]["id"] == graphene.Node.to_global_id(
            "Collection", collection.pk
        )
        assert listing.is_published is False
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"collectionChannelListingUpdate": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["collectionChannelListingUpdate"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: "
            "MANAGE_PRODUCTS"
        )
        assert listing.is_published is True
