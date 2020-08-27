import graphene

from ....product.error_codes import ProductErrorCode
from ....product.models import ProductChannelListing
from ...tests.utils import assert_no_permission, get_graphql_content

PRODUCT_VARIANT_CHANNEL_LISTING_UPDATE_MUTATION = """
mutation UpdateProductVaraintChannelListing(
    $id: ID!,
    $input: [ProductVariantChannelListingAddInput!]!
) {
    productVaraintChannelListingUpdate(id: $id, input: $input) {
        productChannelListingErrors {
            field
            message
            code
            channels
        }
        variant {
            id
            channelListing {
                channel {
                    id
                    slug
                    currencyCode
                }
                price {
                    amount
                    currency
                }
            }
        }
    }
}
"""


def test_variant_channel_listing_update_duplicated_channel(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    variant = product.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": variant_id,
        "input": [
            {"channelId": channel_id, "price": 1},
            {"channelId": channel_id, "price": 2},
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productVaraintChannelListingUpdate"][
        "productChannelListingErrors"
    ]
    assert len(errors) == 1
    assert errors[0]["field"] == "channelId"
    assert errors[0]["code"] == ProductErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["channels"] == [channel_id]


def test_variant_channel_listing_update_with_empty_input(
    staff_api_client, product, permission_manage_products
):
    # given
    variant = product.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "id": variant_id,
        "input": [],
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productVaraintChannelListingUpdate"][
        "productChannelListingErrors"
    ]
    assert not errors


def test_variant_channel_listing_update_not_assigned_channel(
    staff_api_client, product, permission_manage_products, channel_PLN
):
    # given
    variant = product.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": variant_id,
        "input": [{"channelId": channel_id, "price": 1}],
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productVaraintChannelListingUpdate"][
        "productChannelListingErrors"
    ]
    assert len(errors) == 1
    assert errors[0]["field"] == "input"
    assert errors[0]["code"] == ProductErrorCode.PRODUCT_NOT_ASSIGNED_TO_CHANNEL.name
    assert errors[0]["channels"] == [channel_id]


def test_variant_channel_listing_update_negative_price(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    variant = product.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": variant_id,
        "input": [{"channelId": channel_id, "price": -1}],
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productVaraintChannelListingUpdate"][
        "productChannelListingErrors"
    ]
    assert len(errors) == 1
    assert errors[0]["field"] == "price"
    assert errors[0]["code"] == ProductErrorCode.INVALID.name
    assert errors[0]["channels"] == [channel_id]


def test_variant_channel_listing_update_as_staff_user(
    staff_api_client, product, permission_manage_products, channel_USD, channel_PLN
):
    # given
    ProductChannelListing.objects.create(
        product=product, channel=channel_PLN, is_published=True,
    )
    variant = product.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    channel_usd_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": variant_id,
        "input": [
            {"channelId": channel_usd_id, "price": 1},
            {"channelId": channel_pln_id, "price": 20},
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productVaraintChannelListingUpdate"]
    variant_data = data["variant"]
    assert not data["productChannelListingErrors"]
    assert variant_data["id"] == variant_id
    assert variant_data["channelListing"][0]["price"]["currency"] == "USD"
    assert variant_data["channelListing"][0]["price"]["amount"] == 1
    assert variant_data["channelListing"][0]["channel"]["slug"] == channel_USD.slug
    assert variant_data["channelListing"][1]["price"]["currency"] == "PLN"
    assert variant_data["channelListing"][1]["price"]["amount"] == 20
    assert variant_data["channelListing"][1]["channel"]["slug"] == channel_PLN.slug


def test_variant_channel_listing_update_as_app(
    app_api_client, product, permission_manage_products, channel_USD, channel_PLN
):
    # given
    ProductChannelListing.objects.create(
        product=product, channel=channel_PLN, is_published=True,
    )
    variant = product.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    channel_usd_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": variant_id,
        "input": [
            {"channelId": channel_usd_id, "price": 1},
            {"channelId": channel_pln_id, "price": 20},
        ],
    }

    # when
    response = app_api_client.post_graphql(
        PRODUCT_VARIANT_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productVaraintChannelListingUpdate"]
    variant_data = data["variant"]
    assert not data["productChannelListingErrors"]
    assert variant_data["id"] == variant_id
    assert variant_data["channelListing"][0]["price"]["currency"] == "USD"
    assert variant_data["channelListing"][0]["price"]["amount"] == 1
    assert variant_data["channelListing"][0]["channel"]["slug"] == channel_USD.slug
    assert variant_data["channelListing"][1]["price"]["currency"] == "PLN"
    assert variant_data["channelListing"][1]["price"]["amount"] == 20
    assert variant_data["channelListing"][1]["channel"]["slug"] == channel_PLN.slug


def test_variant_channel_listing_update_as_customer(
    user_api_client, product, channel_USD, channel_PLN
):
    # given
    ProductChannelListing.objects.create(
        product=product, channel=channel_PLN, is_published=True,
    )
    variant = product.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    channel_usd_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": variant_id,
        "input": [
            {"channelId": channel_usd_id, "price": 1},
            {"channelId": channel_pln_id, "price": 20},
        ],
    }

    # when
    response = user_api_client.post_graphql(
        PRODUCT_VARIANT_CHANNEL_LISTING_UPDATE_MUTATION, variables=variables,
    )

    # then
    assert_no_permission(response)


def test_variant_channel_listing_update_as_anonymous(
    api_client, product, channel_USD, channel_PLN
):
    # given
    ProductChannelListing.objects.create(
        product=product, channel=channel_PLN, is_published=True,
    )
    variant = product.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    channel_usd_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": variant_id,
        "input": [
            {"channelId": channel_usd_id, "price": 1},
            {"channelId": channel_pln_id, "price": 20},
        ],
    }

    # when
    response = api_client.post_graphql(
        PRODUCT_VARIANT_CHANNEL_LISTING_UPDATE_MUTATION, variables=variables,
    )

    # then
    assert_no_permission(response)
