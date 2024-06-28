from unittest import mock
from unittest.mock import patch

import graphene
from django.test import override_settings

from .....discount.models import PromotionRule
from .....discount.utils.promotion import get_active_catalogue_promotion_rules
from .....graphql.webhook.subscription_payload import get_pre_save_payload_key
from .....product.error_codes import ProductVariantBulkErrorCode
from .....product.models import ProductChannelListing
from .....tests.utils import flush_post_commit_hooks
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.models import Webhook
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
                        path
                        message
                        code
                        warehouses
                        channels
                    }
                    productVariant{
                        metadata {
                            key
                            value
                        }
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


@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_bulk_update.get_webhooks_for_event"
)
@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_product_variant_bulk_update(
    product_variant_created_webhook_mock,
    mocked_get_webhooks_for_event,
    staff_api_client,
    product_with_single_variant,
    size_attribute,
    permission_manage_products,
    any_webhook,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    # given
    variant = product_with_single_variant.variants.last()
    product_id = graphene.Node.to_global_id("Product", product_with_single_variant.pk)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    old_name = variant.name
    new_name = "new-random-name"
    metadata_key = "md key"
    metadata_value = "md value"

    variants = [
        {
            "id": variant_id,
            "name": new_name,
            "metadata": [{"key": metadata_key, "value": metadata_value}],
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
    product_with_single_variant.refresh_from_db(fields=["search_index_dirty"])

    # then
    assert product_with_single_variant.search_index_dirty is True
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    variant_data = data["results"][0]["productVariant"]
    assert variant_data["name"] == new_name
    assert variant_data["metadata"][0]["key"] == metadata_key
    assert variant_data["metadata"][0]["value"] == metadata_value
    assert product_with_single_variant.variants.count() == 1
    assert old_name != new_name
    assert product_variant_created_webhook_mock.call_count == data["count"]
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty


@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_bulk_update.get_webhooks_for_event"
)
def test_product_variant_bulk_update_stocks(
    mocked_get_webhooks_for_event,
    staff_api_client,
    variant_with_many_stocks,
    warehouse,
    permission_manage_products,
    any_webhook,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
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
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty


def test_product_variant_bulk_update_create_already_existing_stock(
    staff_api_client,
    variant_with_many_stocks,
    permission_manage_products,
):
    # given
    variant = variant_with_many_stocks
    product_id = graphene.Node.to_global_id("Product", variant.product_id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    stocks = variant.stocks.all()
    assert len(stocks) == 2
    stock_to_update = stocks[0]

    warehouse_global_id = graphene.Node.to_global_id(
        "Warehouse", stock_to_update.warehouse_id
    )
    variants = [
        {
            "id": variant_id,
            "stocks": {
                "create": [
                    {"quantity": 999, "warehouse": warehouse_global_id},
                ]
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

    data = content["data"]["productVariantBulkUpdate"]

    # then
    errors = data["results"][0]["errors"]
    assert errors
    assert errors[0]["field"] == "warehouse"
    assert errors[0]["path"] == "stocks.create.0.warehouse"
    assert errors[0]["code"] == ProductVariantBulkErrorCode.STOCK_ALREADY_EXISTS.name
    assert errors[0]["warehouses"] == [warehouse_global_id]


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
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty


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
    assert error["path"] == "stocks.create.0.warehouse"
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
    channel_JPY,
    promotion_rule,
):
    # given
    promotion_rule_id = promotion_rule.id
    second_promotion_rule = promotion_rule
    second_promotion_rule.pk = None
    second_promotion_rule.save()
    second_promotion_rule.channels.add(channel_PLN)
    promotion_rule = PromotionRule.objects.get(id=promotion_rule_id)

    product = variant.product
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    ProductChannelListing.objects.create(product=product, channel=channel_PLN)
    existing_variant_listing = variant.channel_listings.get()

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
    get_graphql_content(response, ignore_errors=True)

    # then
    existing_variant_listing.refresh_from_db()
    assert (
        existing_variant_listing.price_amount == new_price_for_existing_variant_listing
    )
    assert (
        existing_variant_listing.discounted_price_amount
        == new_price_for_existing_variant_listing
    )
    new_variant_listing = variant.channel_listings.get(channel=channel_PLN)
    assert new_variant_listing.price_amount == not_existing_variant_listing_price
    assert (
        new_variant_listing.discounted_price_amount
        == not_existing_variant_listing_price
    )

    # only promotions with created channel will be marked as dirty
    second_promotion_rule.refresh_from_db()
    assert second_promotion_rule.variants_dirty is True

    promotion_rule.refresh_from_db()
    assert promotion_rule.variants_dirty is True


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
    assert error["path"] == "channelListings.update.0.price"
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


def test_product_variant_bulk_update_when_variant_not_exists(
    staff_api_client,
    product_with_two_variants,
    permission_manage_products,
):
    # given
    product_id = graphene.Node.to_global_id("Product", product_with_two_variants.pk)
    not_existing_variant_id = graphene.Node.to_global_id("ProductVariant", -1)

    variants = [{"id": not_existing_variant_id, "sku": "NewSku"}]

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
    assert error["path"] == "id"
    assert error["field"] == "id"
    assert error["code"] == ProductVariantBulkErrorCode.INVALID.name


@patch(
    "saleor.graphql.product.bulk_mutations."
    "product_variant_bulk_update.get_webhooks_for_event"
)
def test_product_variant_bulk_update_attributes(
    mocked_get_webhooks_for_event,
    staff_api_client,
    variant_with_many_stocks,
    permission_manage_products,
    any_webhook,
    settings,
    multiselect_attribute,
    color_attribute,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    # given
    variant = variant_with_many_stocks
    product_id = graphene.Node.to_global_id("Product", variant.product_id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    product = variant.product
    product.product_type.variant_attributes.add(multiselect_attribute, color_attribute)
    color_attribute_value = color_attribute.values.first()
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    multiselect_attribute_id = graphene.Node.to_global_id(
        "Attribute", multiselect_attribute.pk
    )

    # ensure that providing as a new value for an attribute, name of an existing value
    # from another attribute will not raise an Error
    variants = [
        {
            "id": variant_id,
            "attributes": [
                {"id": color_attribute_id, "dropdown": {"value": "new-value"}},
                {
                    "id": multiselect_attribute_id,
                    "multiselect": [
                        {"value": color_attribute_value.name},
                        {"value": "test-value-2"},
                    ],
                },
            ],
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
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty


@override_settings(ENABLE_LIMITING_WEBHOOKS_FOR_IDENTICAL_PAYLOADS=True)
@mock.patch(
    "saleor.graphql.product.bulk_mutations.product_variant_bulk_update.ProductVariantBulkUpdate.call_event"
)
def test_generate_pre_save_payloads(
    mocked_call_event,
    staff_api_client,
    variant,
    permission_manage_products,
    webhook_app,
):
    # given
    SUBSCRIPTION_QUERY = """
        subscription {
            event {
                issuedAt
                ... on ProductVariantUpdated {
                    productVariant {
                        name
                    }
                }
            }
        }
    """
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED
    webhook.events.create(event_type=event_type)

    product_id = graphene.Node.to_global_id("Product", variant.product.pk)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variants = [{"id": variant_id, "sku": "NewSku"}]
    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    staff_api_client.post_graphql(PRODUCT_VARIANT_BULK_UPDATE_MUTATION, variables)
    flush_post_commit_hooks()

    # then
    payload_key = get_pre_save_payload_key(webhook, variant)
    request_time = mocked_call_event.call_args[1]["request_time"]
    assert request_time
    pre_save_payload = mocked_call_event.call_args[1]["pre_save_payloads"]
    assert payload_key in pre_save_payload
    assert request_time.isoformat() == pre_save_payload[payload_key]["issuedAt"]
