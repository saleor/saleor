from datetime import date

import graphene
import pytest

from ....product.error_codes import ProductErrorCode
from ...tests.utils import assert_no_permission, get_graphql_content

PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION = """
mutation UpdateProductChannelListing(
    $id: ID!
    $input: ProductChannelListingUpdateInput!
) {
    productChannelListingUpdate(id: $id, input: $input) {
        productsErrors {
            field
            message
            code
            channels
        }
        product {
            slug
            channelListing {
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


def test_product_channel_listing_update_duplicated_ids_in_add_and_remove(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {
            "addChannels": [{"channelId": channel_id, "isPublished": True}],
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
    errors = content["data"]["productChannelListingUpdate"]["productsErrors"]
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
            "addChannels": [
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
    errors = content["data"]["productChannelListingUpdate"]["productsErrors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "addChannels"
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
    errors = content["data"]["productChannelListingUpdate"]["productsErrors"]
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
    errors = content["data"]["productChannelListingUpdate"]["productsErrors"]
    assert not errors


def test_product_channel_listing_update_with_empty_lists_in_input(
    staff_api_client, product, permission_manage_products
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {
        "id": product_id,
        "input": {"addChannels": [], "removeChannels": []},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productChannelListingUpdate"]["productsErrors"]
    assert not errors


def test_product_channel_listing_update_as_staff_user(
    staff_api_client, product, permission_manage_products, channel_USD, channel_PLN
):
    # given
    publication_date = date.today()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": product_id,
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
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]
    assert not data["productsErrors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListing"][0]["isPublished"] is True
    assert product_data["channelListing"][0]["publicationDate"] is None
    assert product_data["channelListing"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListing"][1]["isPublished"] is False
    assert (
        product_data["channelListing"][1]["publicationDate"]
        == publication_date.isoformat()
    )
    assert product_data["channelListing"][1]["channel"]["slug"] == channel_PLN.slug


@pytest.mark.skip(reason="Issue #5845")
def test_product_channel_listing_update_as_app(
    app_api_client, product, permission_manage_products, channel_USD, channel_PLN
):
    # given
    publication_date = date.today()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": product_id,
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
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]
    assert not data["productsErrors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListing"][0]["isPublished"] is True
    assert product_data["channelListing"][0]["publicationDate"] is None
    assert product_data["channelListing"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListing"][1]["isPublished"] is False
    assert (
        product_data["channelListing"][1]["publicationDate"]
        == publication_date.isoformat()
    )
    assert product_data["channelListing"][1]["channel"]["slug"] == channel_PLN.slug


def test_product_channel_listing_update_as_customer(
    user_api_client, product, channel_PLN
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": product_id,
        "input": {"addChannels": [{"channelId": channel_id, "isPublished": False}]},
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
        "input": {"addChannels": [{"channelId": channel_id, "isPublished": False}]},
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
    publication_date = date.today()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": product_id,
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
        PRODUCT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productChannelListingUpdate"]
    product_data = data["product"]
    assert not data["productsErrors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListing"][0]["isPublished"] is True
    assert product_data["channelListing"][0]["publicationDate"] is None
    assert product_data["channelListing"][0]["channel"]["slug"] == channel_USD.slug
    assert product_data["channelListing"][1]["isPublished"] is False
    assert (
        product_data["channelListing"][1]["publicationDate"]
        == publication_date.isoformat()
    )
    assert product_data["channelListing"][1]["channel"]["slug"] == channel_PLN.slug


def test_product_channel_listing_update_unpublish(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {"addChannels": [{"channelId": channel_id, "isPublished": False}]},
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
    assert not data["productsErrors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListing"][0]["isPublished"] is False
    assert product_data["channelListing"][0]["publicationDate"] is None
    assert product_data["channelListing"][0]["channel"]["slug"] == channel_USD.slug


def test_product_channel_listing_update_update_publication_data(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    publication_date = date.today()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": product_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "isPublished": True,
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
    assert not data["productsErrors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListing"][0]["isPublished"] is True
    assert (
        product_data["channelListing"][0]["publicationDate"]
        == publication_date.isoformat()
    )
    assert product_data["channelListing"][0]["channel"]["slug"] == channel_USD.slug


def test_product_channel_listing_update_remove_channel(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
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
    assert not data["productsErrors"]
    assert product_data["slug"] == product.slug
    assert len(product_data["channelListing"]) == 0


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
    assert not data["productsErrors"]
    assert product_data["slug"] == product.slug
    assert product_data["channelListing"][0]["isPublished"] is True
    assert product_data["channelListing"][0]["publicationDate"] is None
    assert product_data["channelListing"][0]["channel"]["slug"] == channel_USD.slug


def test_product_channel_listing_update_publish_product_without_category(
    staff_api_client, product, permission_manage_products, channel_USD, channel_PLN
):
    # given
    product.channel_listing.all().delete()
    product.category = None
    product.save()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    channel_usd_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": product_id,
        "input": {
            "addChannels": [
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
    print(data)
    errors = data["productsErrors"]
    assert errors[0]["field"] == "isPublished"
    assert errors[0]["code"] == ProductErrorCode.PRODUCT_WITHOUT_CATEGORY.name
    assert errors[0]["channels"] == [channel_usd_id]
    assert len(errors) == 1
