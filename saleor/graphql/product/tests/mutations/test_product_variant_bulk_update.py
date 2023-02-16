from unittest.mock import patch

import graphene

from .....product.error_codes import ProductVariantBulkErrorCode
from .....product.models import ProductChannelListing
from .....tests.utils import flush_post_commit_hooks
from ....tests.utils import get_graphql_content

PRODUCT_VARIANT_BULK_UPDATE_MUTATION = """
    mutation ProductVariantBulkUpdate(
        $variants: [ProductVariantBulkUpdateInput!]!,
        $productId: ID!,
        $errorPolicy: ErrorPolicyEnum
    ) {
        productVariantBulkUpdate(
            variants: $variants, product: $productId, errorPolicy: $errorPolicy
            ) {
                results{
                    errors {
                        field
                        message
                        code
                        warehouses
                        channels
                    }
                    productVariant{
                        id
                        name
                        sku
                        stocks {
                            warehouse {
                                slug
                            }
                            quantity
                        }
                        channelListings {
                            channel {
                                slug
                            }
                            price {
                                currency
                                amount
                            }
                            costPrice {
                                currency
                                amount
                            }
                            preorderThreshold {
                                quantity
                            }
                        }
                        preorder {
                            globalThreshold
                            endDate
                        }
                    }
                }
                count
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_product_variant_bulk_update(
    product_variant_created_webhook_mock,
    staff_api_client,
    product_with_single_variant,
    size_attribute,
    permission_manage_products,
):
    # given
    variant = product_with_single_variant.variants.last()
    product_id = graphene.Node.to_global_id("Product", product_with_single_variant.pk)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    old_name = variant.name
    new_name = "new-random-name"

    variants = [{"id": variant_id, "name": new_name}]

    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantBulkUpdate"]

    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    assert data["results"][0]["productVariant"]["name"] == new_name
    assert product_with_single_variant.variants.count() == 1
    assert old_name != new_name
    assert product_variant_created_webhook_mock.call_count == data["count"]


def test_product_variant_bulk_update_stocks(
    staff_api_client,
    variant_with_many_stocks,
    warehouse,
    size_attribute,
    permission_manage_products,
):
    # given
    variant = variant_with_many_stocks
    product_id = graphene.Node.to_global_id("Product", variant.product_id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    stocks = variant.stocks.all()
    assert len(stocks) == 2
    stock_to_update = stocks[0]
    new_quantity = 999
    assert stock_to_update.quantity != new_quantity
    new_stock_quantity = 100

    variants = [
        {
            "id": variant_id,
            "stocks": {
                "create": [
                    {
                        "quantity": new_stock_quantity,
                        "warehouse": graphene.Node.to_global_id(
                            "Warehouse", warehouse.pk
                        ),
                    },
                ],
                "update": [
                    {
                        "quantity": new_quantity,
                        "stock": graphene.Node.to_global_id(
                            "Stock", stock_to_update.pk
                        ),
                    },
                ],
            },
        }
    ]

    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantBulkUpdate"]

    # then
    stock_to_update.refresh_from_db()
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    assert stock_to_update.quantity == new_quantity
    assert variant.stocks.count() == 3
    assert variant.stocks.last().quantity == new_stock_quantity


def test_product_variant_bulk_update_and_remove_stock(
    staff_api_client,
    variant_with_many_stocks,
    warehouse,
    size_attribute,
    permission_manage_products,
):
    # given
    variant = variant_with_many_stocks
    product_id = graphene.Node.to_global_id("Product", variant.product_id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    stocks = variant.stocks.all()
    assert len(stocks) == 2
    stock_to_remove = stocks[0]

    variants = [
        {
            "id": variant_id,
            "stocks": {
                "remove": [graphene.Node.to_global_id("Stock", stock_to_remove.pk)]
            },
        }
    ]

    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantBulkUpdate"]

    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    assert variant.stocks.count() == 1


def test_product_variant_bulk_update_and_remove_stock_when_stock_not_exists(
    staff_api_client,
    variant_with_many_stocks,
    warehouse,
    size_attribute,
    permission_manage_products,
):
    # given
    variant = variant_with_many_stocks
    product_id = graphene.Node.to_global_id("Product", variant.product_id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    stocks = variant.stocks.all()
    assert len(stocks) == 2

    variants = [
        {
            "id": variant_id,
            "stocks": {"remove": [graphene.Node.to_global_id("Stock", "randomID")]},
        }
    ]

    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantBulkUpdate"]

    # then
    assert data["count"] == 0
    assert data["results"][0]["errors"]
    assert variant.stocks.count() == 2
    error = data["results"][0]["errors"][0]
    assert error["code"] == ProductVariantBulkErrorCode.NOT_FOUND.name


def test_product_variant_bulk_update_stocks_with_invalid_warehouse(
    staff_api_client,
    variant_with_many_stocks,
    warehouse,
    size_attribute,
    permission_manage_products,
):
    # given
    variant = variant_with_many_stocks
    product_id = graphene.Node.to_global_id("Product", variant.product_id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    stocks = variant.stocks.all()
    assert len(stocks) == 2
    stock_to_update = stocks[0]
    not_existing_warehouse_id = "aaa="

    variants = [
        {
            "id": variant_id,
            "stocks": {
                "create": [{"quantity": 10, "warehouse": not_existing_warehouse_id}]
            },
        }
    ]

    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantBulkUpdate"]
    stock_to_update.refresh_from_db()

    # then
    assert not data["results"][0]["productVariant"]
    assert data["results"][0]["errors"]
    assert data["count"] == 0
    error = data["results"][0]["errors"][0]
    assert error["field"] == "warehouses"
    assert error["code"] == ProductVariantBulkErrorCode.NOT_FOUND.name
    assert error["warehouses"] == [not_existing_warehouse_id]


def test_product_variant_bulk_update_channel_listings_input(
    staff_api_client,
    variant,
    permission_manage_products,
    warehouses,
    size_attribute,
    channel_USD,
    channel_PLN,
):
    # given
    product = variant.product
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    ProductChannelListing.objects.create(product=product, channel=channel_PLN)
    existing_variant_listing = variant.channel_listings.last()

    assert variant.channel_listings.count() == 1
    product_id = graphene.Node.to_global_id("Product", product.pk)

    new_price_for_existing_variant_listing = 50.0
    not_existing_variant_listing_price = 20.0

    variants = [
        {
            "id": variant_id,
            "channelListings": {
                "update": [
                    {
                        "price": new_price_for_existing_variant_listing,
                        "channelListing": graphene.Node.to_global_id(
                            "ProductVariantChannelListing", existing_variant_listing.id
                        ),
                    }
                ],
                "create": [
                    {
                        "price": not_existing_variant_listing_price,
                        "channelId": graphene.Node.to_global_id(
                            "Channel", channel_PLN.pk
                        ),
                    }
                ],
            },
        },
    ]

    # when
    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response, ignore_errors=True)
    data = content["data"]["productVariantBulkUpdate"]
    existing_variant_listing.refresh_from_db()

    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    assert variant.channel_listings.count() == 2
    new_variant_channel_listing = variant.channel_listings.last()
    assert (
        new_variant_channel_listing.price_amount == not_existing_variant_listing_price
    )
    assert new_variant_channel_listing.channel == channel_PLN
    assert (
        existing_variant_listing.price_amount == new_price_for_existing_variant_listing
    )


def test_product_variant_bulk_update_and_remove_channel_listings(
    staff_api_client,
    variant,
    permission_manage_products,
    warehouses,
    size_attribute,
    channel_USD,
    channel_PLN,
):
    # given
    product = variant.product
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    ProductChannelListing.objects.create(product=product, channel=channel_PLN)
    existing_variant_listing = variant.channel_listings.last()

    assert variant.channel_listings.count() == 1
    product_id = graphene.Node.to_global_id("Product", product.pk)

    variants = [
        {
            "id": variant_id,
            "channelListings": {
                "remove": [
                    graphene.Node.to_global_id(
                        "ProductVariantChannelListing", existing_variant_listing.id
                    )
                ]
            },
        },
    ]

    # when
    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response, ignore_errors=True)
    data = content["data"]["productVariantBulkUpdate"]

    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    assert variant.channel_listings.count() == 0


def test_product_variant_bulk_update_channel_listings_with_invalid_price(
    staff_api_client,
    variant,
    permission_manage_products,
    warehouses,
    size_attribute,
    channel_USD,
    channel_PLN,
):
    # given
    product = variant.product
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    ProductChannelListing.objects.create(product=product, channel=channel_PLN)
    existing_variant_listing = variant.channel_listings.last()

    assert variant.channel_listings.count() == 1
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variants = [
        {
            "id": variant_id,
            "name": "RandomName",
            "channelListings": {
                "update": [
                    {
                        "price": 0.99999,
                        "channelListing": graphene.Node.to_global_id(
                            "ProductVariantChannelListing", existing_variant_listing.pk
                        ),
                    },
                ],
            },
        },
    ]

    # when
    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response, ignore_errors=True)
    data = content["data"]["productVariantBulkUpdate"]
    existing_variant_listing.refresh_from_db()

    # then
    assert data["results"][0]["errors"]
    assert data["count"] == 0
    assert not data["results"][0]["productVariant"]
    error = data["results"][0]["errors"][0]
    assert error["field"] == "price"
    assert error["code"] == ProductVariantBulkErrorCode.INVALID_PRICE.name


def test_product_variant_bulk_update_with_already_existing_sku(
    staff_api_client,
    product_with_two_variants,
    size_attribute,
    permission_manage_products,
):
    # given
    variants = product_with_two_variants.variants.all()
    variant_1 = variants[0]
    variant_2 = variants[1]
    product_id = graphene.Node.to_global_id("Product", product_with_two_variants.pk)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant_1.pk)

    variants = [{"id": variant_id, "sku": variant_2.sku}]

    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantBulkUpdate"]

    # then
    assert data["results"][0]["errors"]
    error = data["results"][0]["errors"][0]
    assert error["field"] == "sku"
    assert error["code"] == ProductVariantBulkErrorCode.UNIQUE.name
