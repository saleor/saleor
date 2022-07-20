import json
from datetime import datetime, timedelta
from unittest.mock import ANY, patch
from uuid import uuid4

import graphene
import pytest
import pytz
from django.utils.text import slugify
from freezegun import freeze_time
from measurement.measures import Weight
from prices import Money, TaxedMoney

from ....attribute import AttributeInputType
from ....attribute.models import AttributeValue
from ....attribute.utils import associate_attribute_values_to_instance
from ....core.exceptions import PreorderAllocationError
from ....core.units import WeightUnits
from ....order import OrderEvents, OrderStatus
from ....order.models import OrderEvent, OrderLine
from ....product.error_codes import ProductErrorCode
from ....product.models import Product, ProductChannelListing, ProductVariant
from ....tests.consts import TEST_SERVER_DOMAIN
from ....tests.utils import dummy_editorjs, flush_post_commit_hooks
from ....warehouse.error_codes import StockErrorCode
from ....warehouse.models import Allocation, Stock, Warehouse
from ...core.enums import WeightUnitsEnum
from ...tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

QUERY_VARIANT = """query ProductVariantDetails(
        $id: ID!, $address: AddressInput, $countryCode: CountryCode, $channel: String
    ) {
        productVariant(id: $id, channel: $channel) {
            id
            deprecatedStocksByCountry: stocks(countryCode: $countryCode) {
                id
            }
            stocksByAddress: stocks(address: $address) {
                id
            }
            attributes {
                attribute {
                    id
                    name
                    slug
                    choices(first: 10) {
                        edges {
                            node {
                                id
                                name
                                slug
                            }
                        }
                    }
                }
                values {
                    id
                    name
                    slug
                }
            }
            media {
                id
            }
            name
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
            }
            product {
                id
            }
            weight {
                unit
                value
            }
            created
        }
    }
"""


def test_fetch_variant(
    staff_api_client,
    product,
    permission_manage_products,
    site_settings,
    channel_USD,
):
    # given
    query = QUERY_VARIANT
    variant = product.variants.first()
    variant.weight = Weight(kg=10)
    variant.save(update_fields=["weight"])

    site_settings.default_weight_unit = WeightUnits.G
    site_settings.save(update_fields=["default_weight_unit"])

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "countryCode": "EU", "channel": channel_USD.slug}
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["name"] == variant.name
    assert data["created"] == variant.created_at.isoformat()

    stocks_count = variant.stocks.count()
    assert len(data["deprecatedStocksByCountry"]) == stocks_count
    assert len(data["stocksByAddress"]) == stocks_count

    assert data["weight"]["value"] == 10000
    assert data["weight"]["unit"] == WeightUnitsEnum.G.name
    channel_listing_data = data["channelListings"][0]
    channel_listing = variant.channel_listings.get()
    assert channel_listing_data["channel"]["slug"] == channel_listing.channel.slug
    assert channel_listing_data["price"]["currency"] == channel_listing.currency
    assert channel_listing_data["price"]["amount"] == channel_listing.price_amount
    assert channel_listing_data["costPrice"]["currency"] == channel_listing.currency
    assert (
        channel_listing_data["costPrice"]["amount"] == channel_listing.cost_price_amount
    )


def test_fetch_variant_no_stocks(
    staff_api_client,
    product,
    permission_manage_products,
    site_settings,
    channel_USD,
):
    # given
    query = QUERY_VARIANT
    variant = product.variants.first()
    variant.weight = Weight(kg=10)
    variant.save(update_fields=["weight"])

    site_settings.default_weight_unit = WeightUnits.G
    site_settings.save(update_fields=["default_weight_unit"])

    warehouse = variant.stocks.first().warehouse
    # remove the warehouse channels
    # the stocks for this warehouse shouldn't be returned
    warehouse.channels.clear()

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "countryCode": "EU", "channel": channel_USD.slug}
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["name"] == variant.name
    assert data["created"] == variant.created_at.isoformat()

    assert not data["deprecatedStocksByCountry"]
    assert not data["stocksByAddress"]

    assert data["weight"]["value"] == 10000
    assert data["weight"]["unit"] == WeightUnitsEnum.G.name
    channel_listing_data = data["channelListings"][0]
    channel_listing = variant.channel_listings.get()
    assert channel_listing_data["channel"]["slug"] == channel_listing.channel.slug
    assert channel_listing_data["price"]["currency"] == channel_listing.currency
    assert channel_listing_data["price"]["amount"] == channel_listing.price_amount
    assert channel_listing_data["costPrice"]["currency"] == channel_listing.currency
    assert (
        channel_listing_data["costPrice"]["amount"] == channel_listing.cost_price_amount
    )


QUERY_PRODUCT_VARIANT_CHANNEL_LISTING = """
    query ProductVariantDetails($id: ID!, $channel: String) {
        productVariant(id: $id, channel: $channel) {
            id
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
                    soldUnits
                }
            }
        }
    }
"""


def test_get_product_variant_channel_listing_as_staff_user(
    staff_api_client,
    product_available_in_many_channels,
    channel_USD,
):
    # given
    variant = product_available_in_many_channels.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_CHANNEL_LISTING,
        variables,
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productVariant"]
    channel_listings = variant.channel_listings.all()
    for channel_listing in channel_listings:
        assert {
            "channel": {"slug": channel_listing.channel.slug},
            "price": {
                "currency": channel_listing.currency,
                "amount": channel_listing.price_amount,
            },
            "costPrice": {
                "currency": channel_listing.currency,
                "amount": channel_listing.cost_price_amount,
            },
            "preorderThreshold": {
                "quantity": channel_listing.preorder_quantity_threshold,
                "soldUnits": 0,
            },
        } in data["channelListings"]
    assert len(data["channelListings"]) == variant.channel_listings.count()


def test_get_product_variant_channel_listing_as_app(
    app_api_client,
    product_available_in_many_channels,
    channel_USD,
):
    # given
    variant = product_available_in_many_channels.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = app_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_CHANNEL_LISTING,
        variables,
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productVariant"]
    channel_listings = variant.channel_listings.all()
    for channel_listing in channel_listings:
        assert {
            "channel": {"slug": channel_listing.channel.slug},
            "price": {
                "currency": channel_listing.currency,
                "amount": channel_listing.price_amount,
            },
            "costPrice": {
                "currency": channel_listing.currency,
                "amount": channel_listing.cost_price_amount,
            },
            "preorderThreshold": {
                "quantity": channel_listing.preorder_quantity_threshold,
                "soldUnits": 0,
            },
        } in data["channelListings"]
    assert len(data["channelListings"]) == variant.channel_listings.count()


def test_get_product_variant_channel_listing_as_customer(
    user_api_client,
    product_available_in_many_channels,
    channel_USD,
):
    # given
    variant = product_available_in_many_channels.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = user_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_CHANNEL_LISTING,
        variables,
    )

    # then
    assert_no_permission(response)


def test_get_product_variant_channel_listing_as_anonymous(
    api_client,
    product_available_in_many_channels,
    channel_USD,
):
    # given
    variant = product_available_in_many_channels.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_CHANNEL_LISTING,
        variables,
    )

    # then
    assert_no_permission(response)


QUERY_PRODUCT_VARIANT_STOCKS = """
  fragment Stock on Stock {
    id
    quantity
    warehouse {
      slug
    }
  }
  query ProductVariantDetails(
    $id: ID!
    $channel: String
    $address: AddressInput
  ) {
    productVariant(id: $id, channel: $channel) {
      id
      stocksNoAddress: stocks {
        ...Stock
      }
      stocksWithAddress: stocks(address: $address) {
        ...Stock
      }
    }
  }
"""


def test_get_product_variant_stocks(
    staff_api_client,
    variant_with_many_stocks_different_shipping_zones,
    channel_USD,
    permission_manage_products,
):
    # given
    variant = variant_with_many_stocks_different_shipping_zones
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "id": variant_id,
        "channel": channel_USD.slug,
        "address": {"country": "PL"},
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_STOCKS,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    all_stocks = variant.stocks.all()
    pl_stocks = variant.stocks.filter(
        warehouse__shipping_zones__countries__contains="PL"
    )
    data = content["data"]["productVariant"]

    # When no address is provided, it should return all stocks of the variant available
    # in given channel.
    assert len(data["stocksNoAddress"]) == all_stocks.count()
    no_address_stocks_ids = [stock["id"] for stock in data["stocksNoAddress"]]
    assert all(
        [
            graphene.Node.to_global_id("Stock", stock.pk) in no_address_stocks_ids
            for stock in all_stocks
        ]
    )

    # When address is given, return only stocks from warehouse that ship to that
    # address.
    assert len(data["stocksWithAddress"]) == pl_stocks.count()
    with_address_stocks_ids = [stock["id"] for stock in data["stocksWithAddress"]]
    assert all(
        [
            graphene.Node.to_global_id("Stock", stock.pk) in with_address_stocks_ids
            for stock in pl_stocks
        ]
    )


def test_get_product_variant_stocks_no_channel_shipping_zones(
    staff_api_client,
    variant_with_many_stocks_different_shipping_zones,
    channel_USD,
    permission_manage_products,
):
    # given
    channel_USD.shipping_zones.clear()
    variant = variant_with_many_stocks_different_shipping_zones
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "id": variant_id,
        "channel": channel_USD.slug,
        "address": {"country": "PL"},
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_STOCKS,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    stocks_count = variant.stocks.count()
    data = content["data"]["productVariant"]
    assert data["stocksNoAddress"] == []
    assert data["stocksWithAddress"] == []
    assert stocks_count > 0


QUERY_PRODUCT_VARIANT_PREORDER = """
    query ProductVariantDetails($id: ID!, $channel: String) {
        productVariant(id: $id, channel: $channel) {
            preorder {
                globalThreshold
                globalSoldUnits
                endDate
            }
        }
    }
"""


def test_get_product_variant_preorder_as_staff(
    staff_api_client,
    preorder_variant_global_and_channel_threshold,
    preorder_allocation,
    channel_USD,
    permission_manage_products,
):
    # given
    variant = preorder_variant_global_and_channel_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_PREORDER,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productVariant"]["preorder"]
    assert data["globalThreshold"] == variant.preorder_global_threshold
    assert data["globalSoldUnits"] == preorder_allocation.quantity
    assert data["endDate"] == variant.preorder_end_date


def test_get_product_variant_preorder_as_customer_not_allowed_fields(
    user_api_client,
    preorder_variant_global_threshold,
    channel_USD,
):
    # given
    variant = preorder_variant_global_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = user_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_PREORDER,
        variables,
    )

    # then
    assert_no_permission(response)


def test_get_product_variant_preorder_as_customer_allowed_fields(
    user_api_client,
    preorder_variant_global_threshold,
    channel_USD,
):
    # given
    variant = preorder_variant_global_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    query = """
        query ProductVariantDetails($id: ID!, $channel: String) {
            productVariant(id: $id, channel: $channel) {
                preorder {
                    endDate
                }
            }
        }
    """
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = user_api_client.post_graphql(
        query,
        variables,
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productVariant"]["preorder"]
    assert data["endDate"] == variant.preorder_end_date


CREATE_VARIANT_MUTATION = """
      mutation createVariant (
            $productId: ID!,
            $sku: String,
            $stocks: [StockInput!],
            $attributes: [AttributeValueInput!]!,
            $weight: WeightScalar,
            $trackInventory: Boolean,
            $preorder: PreorderSettingsInput) {
                productVariantCreate(
                    input: {
                        product: $productId,
                        sku: $sku,
                        stocks: $stocks,
                        attributes: $attributes,
                        trackInventory: $trackInventory,
                        weight: $weight,
                        preorder: $preorder
                    }) {
                    errors {
                      field
                      message
                      attributes
                      code
                    }
                    productVariant {
                        id
                        name
                        sku
                        attributes {
                            attribute {
                                slug
                            }
                            values {
                                name
                                slug
                                reference
                                richText
                                plainText
                                boolean
                                date
                                dateTime
                                file {
                                    url
                                    contentType
                                }
                            }
                        }
                        weight {
                            value
                            unit
                        }
                        stocks {
                            quantity
                            warehouse {
                                slug
                            }
                        }
                        preorder {
                            globalThreshold
                            endDate
                        }
                    }
                }
            }

"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_create_variant(
    updated_webhook_mock,
    created_webhook_mock,
    staff_api_client,
    product,
    product_type,
    permission_manage_products,
    warehouse,
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    weight = 10.22
    variant_slug = product_type.variant_attributes.first().slug
    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().pk
    )
    variant_value = "test-value"
    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "productId": product_id,
        "sku": sku,
        "stocks": stocks,
        "weight": weight,
        "attributes": [{"id": attribute_id, "values": [variant_value]}],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()

    assert not content["errors"]
    data = content["productVariant"]
    assert data["name"] == variant_value
    assert data["sku"] == sku
    assert data["attributes"][0]["attribute"]["slug"] == variant_slug
    assert data["attributes"][0]["values"][0]["slug"] == variant_value
    assert data["weight"]["unit"] == WeightUnitsEnum.KG.name
    assert data["weight"]["value"] == weight
    assert len(data["stocks"]) == 1
    assert data["stocks"][0]["quantity"] == stocks[0]["quantity"]
    assert data["stocks"][0]["warehouse"]["slug"] == warehouse.slug
    created_webhook_mock.assert_called_once_with(product.variants.last())
    updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_create_variant_preorder(
    updated_webhook_mock,
    created_webhook_mock,
    staff_api_client,
    product,
    product_type,
    permission_manage_products,
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().pk
    )
    variant_value = "test-value"
    global_threshold = 10
    end_date = (
        (datetime.now() + timedelta(days=3))
        .astimezone()
        .replace(microsecond=0)
        .isoformat()
    )

    variables = {
        "productId": product_id,
        "sku": "1",
        "weight": 10.22,
        "attributes": [{"id": attribute_id, "values": [variant_value]}],
        "preorder": {
            "globalThreshold": global_threshold,
            "endDate": end_date,
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()

    assert not content["errors"]
    data = content["productVariant"]
    assert data["name"] == variant_value

    assert data["preorder"]["globalThreshold"] == global_threshold
    assert data["preorder"]["endDate"] == end_date
    created_webhook_mock.assert_called_once_with(product.variants.last())
    updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_create_variant_no_required_attributes(
    updated_webhook_mock,
    created_webhook_mock,
    staff_api_client,
    product,
    product_type,
    permission_manage_products,
    warehouse,
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    weight = 10.22

    attribute = product_type.variant_attributes.first()
    attribute.value_required = False
    attribute.save(update_fields=["value_required"])

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "productId": product_id,
        "sku": sku,
        "stocks": stocks,
        "weight": weight,
        "attributes": [],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()

    assert not content["errors"]
    data = content["productVariant"]
    assert data["name"] == sku
    assert data["sku"] == sku
    assert not data["attributes"][0]["values"]
    assert data["weight"]["unit"] == WeightUnitsEnum.KG.name
    assert data["weight"]["value"] == weight
    assert len(data["stocks"]) == 1
    assert data["stocks"][0]["quantity"] == stocks[0]["quantity"]
    assert data["stocks"][0]["warehouse"]["slug"] == warehouse.slug
    created_webhook_mock.assert_called_once_with(product.variants.last())
    updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
def test_create_variant_with_file_attribute(
    created_webhook_mock,
    staff_api_client,
    product,
    product_type,
    file_attribute,
    permission_manage_products,
    warehouse,
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    weight = 10.22

    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(file_attribute)
    file_attr_id = graphene.Node.to_global_id("Attribute", file_attribute.id)
    existing_value = file_attribute.values.first()

    values_count = file_attribute.values.count()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "productId": product_id,
        "sku": sku,
        "stocks": stocks,
        "weight": weight,
        "attributes": [{"id": file_attr_id, "file": existing_value.file_url}],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()

    assert not content["errors"]
    data = content["productVariant"]
    assert data["name"] == sku
    assert data["sku"] == sku
    assert data["attributes"][0]["attribute"]["slug"] == file_attribute.slug
    assert data["attributes"][0]["values"][0]["slug"] == f"{existing_value.slug}-2"
    assert data["attributes"][0]["values"][0]["name"] == existing_value.name
    assert data["weight"]["unit"] == WeightUnitsEnum.KG.name
    assert data["weight"]["value"] == weight
    assert len(data["stocks"]) == 1
    assert data["stocks"][0]["quantity"] == stocks[0]["quantity"]
    assert data["stocks"][0]["warehouse"]["slug"] == warehouse.slug

    file_attribute.refresh_from_db()
    assert file_attribute.values.count() == values_count + 1

    created_webhook_mock.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
def test_create_variant_with_boolean_attribute(
    created_webhook_mock,
    permission_manage_products,
    product,
    product_type,
    staff_api_client,
    boolean_attribute,
    size_attribute,
    warehouse,
):
    product_type.variant_attributes.add(
        boolean_attribute, through_defaults={"variant_selection": True}
    )
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    boolean_attr_id = graphene.Node.to_global_id("Attribute", boolean_attribute.id)
    size_attr_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)

    variables = {
        "productId": product_id,
        "sku": "1",
        "stocks": [
            {
                "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
                "quantity": 20,
            }
        ],
        "costPrice": 3.22,
        "price": 1.32,
        "weight": 10.22,
        "attributes": [
            {"id": boolean_attr_id, "boolean": True},
            {"id": size_attr_id, "values": ["XXXL"]},
        ],
        "trackInventory": True,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()
    data = content["productVariant"]

    assert not content["errors"]
    assert data["name"] == "Boolean: Yes / XXXL"
    expected_attribute_data = {
        "attribute": {"slug": "boolean"},
        "values": [
            {
                "name": "Boolean: Yes",
                "slug": f"{boolean_attribute.id}_true",
                "reference": None,
                "richText": None,
                "plainText": None,
                "boolean": True,
                "file": None,
                "dateTime": None,
                "date": None,
            }
        ],
    }

    assert expected_attribute_data in data["attributes"]
    created_webhook_mock.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
def test_create_variant_with_file_attribute_new_value(
    created_webhook_mock,
    staff_api_client,
    product,
    product_type,
    file_attribute,
    permission_manage_products,
    warehouse,
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    price = 1.32
    cost_price = 3.22
    weight = 10.22

    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(file_attribute)
    file_attr_id = graphene.Node.to_global_id("Attribute", file_attribute.id)
    new_value = "new_value.txt"

    values_count = file_attribute.values.count()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "productId": product_id,
        "sku": sku,
        "stocks": stocks,
        "costPrice": cost_price,
        "price": price,
        "weight": weight,
        "attributes": [{"id": file_attr_id, "file": new_value}],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()

    assert not content["errors"]
    data = content["productVariant"]
    assert data["name"] == sku
    assert data["sku"] == sku
    assert data["attributes"][0]["attribute"]["slug"] == file_attribute.slug
    assert data["attributes"][0]["values"][0]["slug"] == slugify(new_value)
    assert data["weight"]["unit"] == WeightUnitsEnum.KG.name
    assert data["weight"]["value"] == weight
    assert len(data["stocks"]) == 1
    assert data["stocks"][0]["quantity"] == stocks[0]["quantity"]
    assert data["stocks"][0]["warehouse"]["slug"] == warehouse.slug

    file_attribute.refresh_from_db()
    assert file_attribute.values.count() == values_count + 1

    created_webhook_mock.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
def test_create_variant_with_file_attribute_no_file_url_given(
    created_webhook_mock,
    staff_api_client,
    product,
    product_type,
    file_attribute,
    permission_manage_products,
    warehouse,
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    price = 1.32
    cost_price = 3.22
    weight = 10.22

    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(file_attribute)
    file_attr_id = graphene.Node.to_global_id("Attribute", file_attribute.id)

    values_count = file_attribute.values.count()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "productId": product_id,
        "sku": sku,
        "stocks": stocks,
        "costPrice": cost_price,
        "price": price,
        "weight": weight,
        "attributes": [{"id": file_attr_id}],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()

    errors = content["errors"]
    data = content["productVariant"]
    assert not errors
    assert data["name"] == sku
    assert data["sku"] == sku
    assert data["attributes"][0]["attribute"]["slug"] == file_attribute.slug
    assert len(data["attributes"][0]["values"]) == 0
    assert data["weight"]["unit"] == WeightUnitsEnum.KG.name
    assert data["weight"]["value"] == weight
    assert len(data["stocks"]) == 1
    assert data["stocks"][0]["quantity"] == stocks[0]["quantity"]
    assert data["stocks"][0]["warehouse"]["slug"] == warehouse.slug

    file_attribute.refresh_from_db()
    assert file_attribute.values.count() == values_count

    created_webhook_mock.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
def test_create_variant_with_page_reference_attribute(
    created_webhook_mock,
    staff_api_client,
    product,
    product_type,
    product_type_page_reference_attribute,
    page_list,
    permission_manage_products,
    warehouse,
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"

    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(product_type_page_reference_attribute)
    ref_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.id
    )

    page_ref_1 = graphene.Node.to_global_id("Page", page_list[0].pk)
    page_ref_2 = graphene.Node.to_global_id("Page", page_list[1].pk)

    values_count = product_type_page_reference_attribute.values.count()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "productId": product_id,
        "sku": sku,
        "stocks": stocks,
        "attributes": [{"id": ref_attr_id, "references": [page_ref_1, page_ref_2]}],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()

    assert not content["errors"]
    data = content["productVariant"]
    assert data["sku"] == sku
    variant_id = data["id"]
    _, variant_pk = graphene.Node.from_global_id(variant_id)
    assert (
        data["attributes"][0]["attribute"]["slug"]
        == product_type_page_reference_attribute.slug
    )
    expected_values = [
        {
            "slug": f"{variant_pk}_{page_list[0].pk}",
            "file": None,
            "richText": None,
            "plainText": None,
            "reference": page_ref_1,
            "name": page_list[0].title,
            "boolean": None,
            "date": None,
            "dateTime": None,
        },
        {
            "slug": f"{variant_pk}_{page_list[1].pk}",
            "file": None,
            "richText": None,
            "plainText": None,
            "reference": page_ref_2,
            "name": page_list[1].title,
            "boolean": None,
            "date": None,
            "dateTime": None,
        },
    ]
    for value in expected_values:
        assert value in data["attributes"][0]["values"]
    assert len(data["stocks"]) == 1
    assert data["stocks"][0]["quantity"] == stocks[0]["quantity"]
    assert data["stocks"][0]["warehouse"]["slug"] == warehouse.slug

    product_type_page_reference_attribute.refresh_from_db()
    assert product_type_page_reference_attribute.values.count() == values_count + 2

    created_webhook_mock.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
def test_create_variant_with_page_reference_attribute_no_references_given(
    created_webhook_mock,
    updated_webhook_mock,
    staff_api_client,
    product,
    product_type,
    product_type_page_reference_attribute,
    permission_manage_products,
    warehouse,
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"

    product_type_page_reference_attribute.value_required = True
    product_type_page_reference_attribute.save(update_fields=["value_required"])

    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(product_type_page_reference_attribute)
    ref_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.id
    )

    values_count = product_type_page_reference_attribute.values.count()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "productId": product_id,
        "sku": sku,
        "stocks": stocks,
        "attributes": [{"id": ref_attr_id, "file": "test.jpg"}],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()
    errors = content["errors"]
    data = content["productVariant"]

    assert not data
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [ref_attr_id]

    product_type_page_reference_attribute.refresh_from_db()
    assert product_type_page_reference_attribute.values.count() == values_count

    created_webhook_mock.assert_not_called()
    updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
def test_create_variant_with_product_reference_attribute(
    created_webhook_mock,
    staff_api_client,
    product,
    product_type,
    product_type_product_reference_attribute,
    product_list,
    permission_manage_products,
    warehouse,
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"

    product_type_product_reference_attribute.value_required = True
    product_type_product_reference_attribute.save(update_fields=["value_required"])

    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(product_type_product_reference_attribute)
    ref_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.id
    )

    product_ref_1 = graphene.Node.to_global_id("Product", product_list[0].pk)
    product_ref_2 = graphene.Node.to_global_id("Product", product_list[1].pk)

    values_count = product_type_product_reference_attribute.values.count()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "productId": product_id,
        "sku": sku,
        "stocks": stocks,
        "attributes": [
            {"id": ref_attr_id, "references": [product_ref_1, product_ref_2]}
        ],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()

    assert not content["errors"]
    data = content["productVariant"]
    assert data["sku"] == sku
    variant_id = data["id"]
    _, variant_pk = graphene.Node.from_global_id(variant_id)
    assert (
        data["attributes"][0]["attribute"]["slug"]
        == product_type_product_reference_attribute.slug
    )
    expected_values = [
        {
            "slug": f"{variant_pk}_{product_list[0].pk}",
            "file": None,
            "richText": None,
            "plainText": None,
            "reference": product_ref_1,
            "name": product_list[0].name,
            "boolean": None,
            "date": None,
            "dateTime": None,
        },
        {
            "slug": f"{variant_pk}_{product_list[1].pk}",
            "file": None,
            "richText": None,
            "plainText": None,
            "reference": product_ref_2,
            "name": product_list[1].name,
            "boolean": None,
            "date": None,
            "dateTime": None,
        },
    ]
    for value in expected_values:
        assert value in data["attributes"][0]["values"]
    assert len(data["stocks"]) == 1
    assert data["stocks"][0]["quantity"] == stocks[0]["quantity"]
    assert data["stocks"][0]["warehouse"]["slug"] == warehouse.slug

    product_type_product_reference_attribute.refresh_from_db()
    assert product_type_product_reference_attribute.values.count() == values_count + 2

    created_webhook_mock.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
def test_create_variant_with_product_reference_attribute_no_references_given(
    created_webhook_mock,
    updated_webhook_mock,
    staff_api_client,
    product,
    product_type,
    product_type_product_reference_attribute,
    permission_manage_products,
    warehouse,
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"

    product_type_product_reference_attribute.value_required = True
    product_type_product_reference_attribute.save(update_fields=["value_required"])

    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(product_type_product_reference_attribute)
    ref_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.id
    )

    values_count = product_type_product_reference_attribute.values.count()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "productId": product_id,
        "sku": sku,
        "stocks": stocks,
        "attributes": [{"id": ref_attr_id, "file": "test.jpg"}],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()
    errors = content["errors"]
    data = content["productVariant"]

    assert not data
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [ref_attr_id]

    product_type_product_reference_attribute.refresh_from_db()
    assert product_type_product_reference_attribute.values.count() == values_count

    created_webhook_mock.assert_not_called()
    updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
def test_create_variant_with_numeric_attribute(
    created_webhook_mock,
    staff_api_client,
    product,
    product_type,
    permission_manage_products,
    warehouse,
    numeric_attribute,
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    weight = 10.22
    product_type.variant_attributes.set([numeric_attribute])
    variant_slug = numeric_attribute.slug
    attribute_id = graphene.Node.to_global_id("Attribute", numeric_attribute.pk)
    variant_value = "22.31"
    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "productId": product_id,
        "sku": sku,
        "stocks": stocks,
        "weight": weight,
        "attributes": [{"id": attribute_id, "values": [variant_value]}],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    assert not content["errors"]
    data = content["productVariant"]
    variant_pk = graphene.Node.from_global_id(data["id"])[1]
    assert data["name"] == sku
    assert data["sku"] == sku
    assert data["attributes"][0]["attribute"]["slug"] == variant_slug
    assert (
        data["attributes"][0]["values"][0]["slug"]
        == f"{variant_pk}_{numeric_attribute.pk}"
    )
    assert data["weight"]["unit"] == WeightUnitsEnum.KG.name
    assert data["weight"]["value"] == weight
    assert len(data["stocks"]) == 1
    assert data["stocks"][0]["quantity"] == stocks[0]["quantity"]
    assert data["stocks"][0]["warehouse"]["slug"] == warehouse.slug
    created_webhook_mock.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_create_variant_with_numeric_attribute_not_numeric_value_given(
    updated_webhook_mock,
    staff_api_client,
    product,
    product_type,
    permission_manage_products,
    warehouse,
    numeric_attribute,
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    weight = 10.22
    product_type.variant_attributes.set([numeric_attribute])
    attribute_id = graphene.Node.to_global_id("Attribute", numeric_attribute.pk)
    variant_value = "abd"
    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "productId": product_id,
        "sku": sku,
        "stocks": stocks,
        "weight": weight,
        "attributes": [{"id": attribute_id, "values": [variant_value]}],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantCreate"]
    error = data["errors"][0]
    assert not data["productVariant"]
    assert error["field"] == "attributes"
    assert error["code"] == ProductErrorCode.INVALID.name

    updated_webhook_mock.assert_not_called()


def test_create_product_variant_with_negative_weight(
    staff_api_client, product, product_type, permission_manage_products
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().pk
    )
    variant_value = "test-value"

    variables = {
        "productId": product_id,
        "weight": -1,
        "attributes": [{"id": attribute_id, "values": [variant_value]}],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantCreate"]
    error = data["errors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


def test_create_product_variant_required_without_attributes(
    staff_api_client, product, permission_manage_products
):
    # given
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute = product.product_type.variant_attributes.first()
    attribute.value_required = True
    attribute.save(update_fields=["value_required"])

    variables = {
        "productId": product_id,
        "sku": "test-sku",
        "price": 0,
        "attributes": [],
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantCreate"]
    error = data["errors"][0]

    assert error["field"] == "attributes"
    assert error["code"] == ProductErrorCode.REQUIRED.name


def test_create_product_variant_missing_required_attributes(
    staff_api_client, product, product_type, color_attribute, permission_manage_products
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().pk
    )
    variant_value = "test-value"

    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    product_type.variant_attributes.add(
        color_attribute, through_defaults={"variant_selection": True}
    )

    variables = {
        "productId": product_id,
        "sku": sku,
        "attributes": [{"id": attribute_id, "values": [variant_value]}],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["productVariantCreate"]["errors"]
    assert content["data"]["productVariantCreate"]["errors"][0] == {
        "field": "attributes",
        "code": ProductErrorCode.REQUIRED.name,
        "message": ANY,
        "attributes": [graphene.Node.to_global_id("Attribute", color_attribute.pk)],
    }
    assert not product.variants.filter(sku=sku).exists()


def test_create_product_variant_duplicated_attributes(
    staff_api_client,
    product_with_variant_with_two_attributes,
    color_attribute,
    size_attribute,
    permission_manage_products,
):
    query = CREATE_VARIANT_MUTATION
    product = product_with_variant_with_two_attributes
    product_id = graphene.Node.to_global_id("Product", product.pk)
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.id)
    sku = str(uuid4())[:12]
    variables = {
        "productId": product_id,
        "sku": sku,
        "attributes": [
            {"id": color_attribute_id, "values": ["red"]},
            {"id": size_attribute_id, "values": ["small"]},
        ],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["productVariantCreate"]["errors"]
    assert content["data"]["productVariantCreate"]["errors"][0] == {
        "field": "attributes",
        "code": ProductErrorCode.DUPLICATED_INPUT_ITEM.name,
        "message": ANY,
        "attributes": [color_attribute_id, size_attribute_id],
    }
    assert not product.variants.filter(sku=sku).exists()


def test_create_variant_invalid_variant_attributes(
    staff_api_client,
    product,
    product_type,
    permission_manage_products,
    warehouse,
    color_attribute,
    weight_attribute,
    rich_text_attribute,
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    price = 1.32
    cost_price = 3.22
    weight = 10.22

    # Default attribute defined in product_type fixture
    size_attribute = product_type.variant_attributes.get(name="Size")
    size_value_slug = size_attribute.values.first().slug
    size_attr_id = graphene.Node.to_global_id("Attribute", size_attribute.id)

    # Add second attribute
    product_type.variant_attributes.add(color_attribute)
    color_attr_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    non_existent_attr_value = "The cake is a lie"

    # Add third attribute
    product_type.variant_attributes.add(weight_attribute)
    weight_attr_id = graphene.Node.to_global_id("Attribute", weight_attribute.id)

    # Add fourth attribute
    rich_text_attribute.value_required = True
    rich_text_attribute.save()
    product_type.variant_attributes.add(rich_text_attribute)
    rich_text_attr_id = graphene.Node.to_global_id("Attribute", rich_text_attribute.id)

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "productId": product_id,
        "sku": sku,
        "stocks": stocks,
        "costPrice": cost_price,
        "price": price,
        "weight": weight,
        "attributes": [
            {"id": color_attr_id, "values": [" "]},
            {"id": weight_attr_id, "values": [" "]},
            {"id": size_attr_id, "values": [non_existent_attr_value, size_value_slug]},
            {"id": rich_text_attr_id, "richText": json.dumps(dummy_editorjs(" "))},
        ],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    data = content["data"]["productVariantCreate"]
    errors = data["errors"]

    assert not data["productVariant"]
    assert len(errors) == 3

    expected_errors = [
        {
            "attributes": [color_attr_id, weight_attr_id],
            "code": ProductErrorCode.REQUIRED.name,
            "field": "attributes",
            "message": ANY,
        },
        {
            "attributes": [size_attr_id],
            "code": ProductErrorCode.INVALID.name,
            "field": "attributes",
            "message": ANY,
        },
        {
            "attributes": [rich_text_attr_id],
            "code": ProductErrorCode.REQUIRED.name,
            "field": "attributes",
            "message": ANY,
        },
    ]
    for error in expected_errors:
        assert error in errors


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
def test_create_variant_with_rich_text_attribute(
    created_webhook_mock,
    permission_manage_products,
    product,
    product_type,
    staff_api_client,
    rich_text_attribute,
    warehouse,
):
    product_type.variant_attributes.add(rich_text_attribute)
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    price = 1.32
    cost_price = 3.22
    weight = 10.22
    attr_id = graphene.Node.to_global_id("Attribute", rich_text_attribute.id)
    rich_text = json.dumps(dummy_editorjs("Sample text"))
    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]
    variables = {
        "productId": product_id,
        "sku": sku,
        "stocks": stocks,
        "costPrice": cost_price,
        "price": price,
        "weight": weight,
        "attributes": [
            {"id": attr_id, "richText": rich_text},
        ],
        "trackInventory": True,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()
    data = content["productVariant"]

    assert not content["errors"]
    assert data["name"] == sku
    assert data["sku"] == sku
    assert data["attributes"][-1]["values"][0]["richText"] == rich_text
    created_webhook_mock.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
def test_create_variant_with_plain_text_attribute(
    created_webhook_mock,
    permission_manage_products,
    product,
    product_type,
    staff_api_client,
    plain_text_attribute,
    warehouse,
):
    # given
    product_type.variant_attributes.add(plain_text_attribute)
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    price = 1.32
    cost_price = 3.22
    weight = 10.22
    attr_id = graphene.Node.to_global_id("Attribute", plain_text_attribute.id)
    text = "Sample text"
    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]
    variables = {
        "productId": product_id,
        "sku": sku,
        "stocks": stocks,
        "costPrice": cost_price,
        "price": price,
        "weight": weight,
        "attributes": [
            {"id": attr_id, "plainText": text},
        ],
        "trackInventory": True,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()
    data = content["productVariant"]

    assert not content["errors"]
    assert data["name"] == sku
    assert data["sku"] == sku
    assert data["attributes"][-1]["values"][0]["plainText"] == text
    created_webhook_mock.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
@freeze_time(datetime(2020, 5, 5, 5, 5, 5, tzinfo=pytz.utc))
def test_create_variant_with_date_attribute(
    created_webhook_mock,
    permission_manage_products,
    product,
    product_type,
    staff_api_client,
    date_attribute,
    warehouse,
):
    product_type.variant_attributes.add(date_attribute)

    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    price = 1.32
    weight = 10.22
    date_attribute_id = graphene.Node.to_global_id("Attribute", date_attribute.id)
    date_time_value = datetime.now(tz=pytz.utc)
    date_value = date_time_value.date()

    variables = {
        "productId": product_id,
        "sku": sku,
        "price": price,
        "weight": weight,
        "attributes": [
            {"id": date_attribute_id, "date": date_value},
        ],
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()
    data = content["productVariant"]
    variant = product.variants.last()
    expected_attributes_data = {
        "attribute": {"slug": "release-date"},
        "values": [
            {
                "boolean": None,
                "file": None,
                "reference": None,
                "richText": None,
                "plainText": None,
                "dateTime": None,
                "date": str(date_value),
                "name": str(date_value),
                "slug": f"{variant.id}_{date_attribute.id}",
            }
        ],
    }

    assert not content["errors"]
    assert data["sku"] == sku
    assert expected_attributes_data in data["attributes"]

    created_webhook_mock.assert_called_once_with(variant)


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
@freeze_time(datetime(2020, 5, 5, 5, 5, 5, tzinfo=pytz.utc))
def test_create_variant_with_date_time_attribute(
    created_webhook_mock,
    permission_manage_products,
    product,
    product_type,
    staff_api_client,
    date_time_attribute,
    warehouse,
):
    product_type.variant_attributes.add(date_time_attribute)

    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    price = 1.32
    weight = 10.22
    date_time_attribute_id = graphene.Node.to_global_id(
        "Attribute", date_time_attribute.id
    )
    date_time_value = datetime.now(tz=pytz.utc)

    variables = {
        "productId": product_id,
        "sku": sku,
        "price": price,
        "weight": weight,
        "attributes": [
            {"id": date_time_attribute_id, "dateTime": date_time_value},
        ],
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()
    data = content["productVariant"]
    variant = product.variants.last()
    expected_attributes_data = {
        "attribute": {"slug": "release-date-time"},
        "values": [
            {
                "boolean": None,
                "file": None,
                "reference": None,
                "richText": None,
                "plainText": None,
                "dateTime": date_time_value.isoformat(),
                "date": None,
                "name": str(date_time_value),
                "slug": f"{variant.id}_{date_time_attribute.id}",
            }
        ],
    }

    assert not content["errors"]
    assert data["sku"] == sku
    assert expected_attributes_data in data["attributes"]

    created_webhook_mock.assert_called_once_with(variant)


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_create_variant_with_empty_string_for_sku(
    updated_webhook_mock,
    created_webhook_mock,
    staff_api_client,
    product,
    product_type,
    permission_manage_products,
    warehouse,
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = ""
    weight = 10.22
    variant_slug = product_type.variant_attributes.first().slug
    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().pk
    )
    variant_value = "test-value"
    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "productId": product_id,
        "sku": sku,
        "stocks": stocks,
        "weight": weight,
        "attributes": [{"id": attribute_id, "values": [variant_value]}],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()

    assert not content["errors"]
    data = content["productVariant"]
    assert data["name"] == variant_value
    assert data["sku"] is None
    assert data["attributes"][0]["attribute"]["slug"] == variant_slug
    assert data["attributes"][0]["values"][0]["slug"] == variant_value
    assert data["weight"]["unit"] == WeightUnitsEnum.KG.name
    assert data["weight"]["value"] == weight
    assert len(data["stocks"]) == 1
    assert data["stocks"][0]["quantity"] == stocks[0]["quantity"]
    assert data["stocks"][0]["warehouse"]["slug"] == warehouse.slug
    created_webhook_mock.assert_called_once_with(product.variants.last())
    updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_create_variant_without_sku(
    updated_webhook_mock,
    created_webhook_mock,
    staff_api_client,
    product,
    product_type,
    permission_manage_products,
    warehouse,
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    weight = 10.22
    variant_slug = product_type.variant_attributes.first().slug
    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().pk
    )
    variant_value = "test-value"
    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "productId": product_id,
        "stocks": stocks,
        "weight": weight,
        "attributes": [{"id": attribute_id, "values": [variant_value]}],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()

    assert not content["errors"]
    data = content["productVariant"]
    assert data["name"] == variant_value
    assert data["sku"] is None
    assert data["attributes"][0]["attribute"]["slug"] == variant_slug
    assert data["attributes"][0]["values"][0]["slug"] == variant_value
    assert data["weight"]["unit"] == WeightUnitsEnum.KG.name
    assert data["weight"]["value"] == weight
    assert len(data["stocks"]) == 1
    assert data["stocks"][0]["quantity"] == stocks[0]["quantity"]
    assert data["stocks"][0]["warehouse"]["slug"] == warehouse.slug
    created_webhook_mock.assert_called_once_with(product.variants.last())
    updated_webhook_mock.assert_not_called()


def test_product_variant_update_with_new_attributes(
    staff_api_client, permission_manage_products, product, size_attribute
):
    query = """
        mutation VariantUpdate(
          $id: ID!
          $attributes: [AttributeValueInput!]
          $sku: String
          $trackInventory: Boolean!
        ) {
          productVariantUpdate(
            id: $id
            input: {
              attributes: $attributes
              sku: $sku
              trackInventory: $trackInventory
            }
          ) {
            errors {
              field
              message
            }
            productVariant {
              id
              attributes {
                attribute {
                  id
                  name
                  slug
                  choices(first:10) {
                    edges {
                      node {
                        id
                        name
                        slug
                        __typename
                      }
                    }
                  }
                  __typename
                }
                __typename
              }
            }
          }
        }
    """

    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    variant_id = graphene.Node.to_global_id(
        "ProductVariant", product.variants.first().pk
    )
    attr_value = "XXXL"

    variables = {
        "attributes": [{"id": size_attribute_id, "values": [attr_value]}],
        "id": variant_id,
        "sku": "21599567",
        "trackInventory": True,
    }

    data = get_graphql_content(
        staff_api_client.post_graphql(
            query, variables, permissions=[permission_manage_products]
        )
    )["data"]["productVariantUpdate"]
    assert not data["errors"]
    assert data["productVariant"]["id"] == variant_id

    attributes = data["productVariant"]["attributes"]
    assert len(attributes) == 1
    assert attributes[0]["attribute"]["id"] == size_attribute_id


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_update_product_variant(
    product_variant_updated_webhook_mock,
    product_variant_created_webhook_mock,
    staff_api_client,
    product,
    size_attribute,
    permission_manage_products,
):
    query = """
        mutation updateVariant (
            $id: ID!,
            $sku: String!,
            $quantityLimitPerCustomer: Int!
            $trackInventory: Boolean!,
            $attributes: [AttributeValueInput!]) {
                productVariantUpdate(
                    id: $id,
                    input: {
                        sku: $sku,
                        trackInventory: $trackInventory,
                        attributes: $attributes,
                        quantityLimitPerCustomer: $quantityLimitPerCustomer,
                    }) {
                    productVariant {
                        name
                        sku
                        quantityLimitPerCustomer
                        channelListings {
                            channel {
                                slug
                            }
                        }
                    }
                }
            }

    """
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    sku = "test sku"
    quantity_limit_per_customer = 5
    attr_value = "S"

    variables = {
        "id": variant_id,
        "sku": sku,
        "trackInventory": True,
        "quantityLimitPerCustomer": quantity_limit_per_customer,
        "attributes": [{"id": attribute_id, "values": [attr_value]}],
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantUpdate"]["productVariant"]

    assert data["name"] == variant.name
    assert data["sku"] == sku
    assert data["quantityLimitPerCustomer"] == quantity_limit_per_customer
    product_variant_updated_webhook_mock.assert_called_once_with(
        product.variants.last()
    )
    product_variant_created_webhook_mock.assert_not_called()


def test_update_product_variant_with_negative_weight(
    staff_api_client, product, permission_manage_products
):
    query = """
        mutation updateVariant (
            $id: ID!,
            $weight: WeightScalar
        ) {
            productVariantUpdate(
                id: $id,
                input: {
                    weight: $weight,
                }
            ){
                productVariant {
                    name
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "weight": -1}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]
    error = data["errors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


@pytest.mark.parametrize("quantity_value", [0, -10])
def test_update_product_variant_limit_per_customer_lower_than_1(
    staff_api_client, product, permission_manage_products, quantity_value
):
    query = """
        mutation updateVariant (
            $id: ID!,
            $quantityLimitPerCustomer: Int
        ) {
            productVariantUpdate(
                id: $id,
                input: {
                    quantityLimitPerCustomer: $quantityLimitPerCustomer,
                }
            ){
                errors {
                    field
                    message
                    code
                }
            }
        }
    """
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "quantityLimitPerCustomer": quantity_value}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]
    error = data["errors"][0]
    assert error["field"] == "quantityLimitPerCustomer"
    assert error["code"] == ProductErrorCode.INVALID.name


QUERY_UPDATE_VARIANT_SKU = """
    mutation updateVariant (
        $id: ID!,
        $sku: String
    ) {
        productVariantUpdate(
            id: $id,
            input: {
                sku: $sku
            }
        ){
            productVariant {
                sku
            }
            errors {
                field
                code
            }
        }
    }
"""


def test_update_product_variant_change_sku(
    staff_api_client, product, permission_manage_products
):
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "n3wSKU"
    variables = {"id": variant_id, "sku": sku}
    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_SKU, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]["productVariant"]
    assert data["sku"] == sku
    variant.refresh_from_db()
    assert variant.sku == sku


def test_update_product_variant_without_sku_keep_it_empty(
    staff_api_client, product, permission_manage_products
):
    variant = product.variants.first()
    variant.sku = None
    variant.save()

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "sku": ""}
    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_SKU, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]
    assert data["productVariant"]["sku"] is None
    assert not data["errors"]
    variant.refresh_from_db()
    assert variant.sku is None


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_update_product_variant_change_sku_to_empty_string(
    product_variant_updated_webhook_mock,
    product_variant_created_webhook_mock,
    staff_api_client,
    product,
    permission_manage_products,
):
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "sku": ""}
    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_SKU, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]["productVariant"]

    assert data["sku"] is None
    product_variant_updated_webhook_mock.assert_called_once_with(
        product.variants.last()
    )
    product_variant_created_webhook_mock.assert_not_called()


QUERY_UPDATE_VARIANT_ATTRIBUTES = """
    mutation updateVariant (
        $id: ID!,
        $sku: String,
        $attributes: [AttributeValueInput!]) {
            productVariantUpdate(
                id: $id,
                input: {
                    sku: $sku,
                    attributes: $attributes
                }) {
                productVariant {
                    sku
                    attributes {
                        attribute {
                            slug
                        }
                        values {
                            id
                            slug
                            name
                            file {
                                url
                                contentType
                            }
                            reference
                            richText
                            plainText
                            boolean
                            date
                            dateTime
                        }
                    }
                }
                errors {
                    field
                    code
                    message
                }
            }
        }
"""


def test_update_product_variant_do_not_require_required_attributes(
    staff_api_client, product, product_type, permission_manage_products
):
    """Ensures product variant can be updated without providing required attributes."""

    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "test sku"
    attr = product_type.variant_attributes.first()
    attr.value_required = True
    attr.save(update_fields=["value_required"])

    variables = {
        "id": variant_id,
        "sku": sku,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]
    assert not len(data["errors"])
    assert data["productVariant"]["sku"] == sku
    assert len(data["productVariant"]["attributes"]) == 1
    assert data["productVariant"]["attributes"][0]["values"]


def test_update_product_variant_with_current_attribute(
    staff_api_client,
    product_with_variant_with_two_attributes,
    color_attribute,
    size_attribute,
    permission_manage_products,
):
    product = product_with_variant_with_two_attributes
    variant = product.variants.first()
    sku = str(uuid4())[:12]
    assert not variant.sku == sku
    assert variant.attributes.first().values.first().slug == "red"
    assert variant.attributes.last().values.first().slug == "small"

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": color_attribute_id, "values": ["red"]},
            {"id": size_attribute_id, "values": ["small"]},
        ],
    }

    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_ATTRIBUTES,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    data = content["data"]["productVariantUpdate"]
    assert not data["errors"]
    variant.refresh_from_db()
    assert variant.sku == sku
    assert variant.attributes.first().values.first().slug == "red"
    assert variant.attributes.last().values.first().slug == "small"


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_update_variant_with_boolean_attribute(
    product_variant_updated,
    permission_manage_products,
    product,
    product_type,
    staff_api_client,
    boolean_attribute,
    warehouse,
    size_attribute,
):
    product_type.variant_attributes.add(boolean_attribute)
    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "123"
    attr_id = graphene.Node.to_global_id("Attribute", boolean_attribute.id)
    size_attr_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)

    new_value = False
    values_count = boolean_attribute.values.count()
    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": size_attr_id, "values": ["XXXL"]},
            {"id": attr_id, "boolean": new_value},
        ],
    }

    associate_attribute_values_to_instance(
        variant, boolean_attribute, boolean_attribute.values.first()
    )

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantUpdate"]
    variant.refresh_from_db()
    data = content["productVariant"]

    assert not content["errors"]
    assert data["sku"] == sku
    assert data["attributes"][-1]["attribute"]["slug"] == boolean_attribute.slug
    assert data["attributes"][-1]["values"][0]["name"] == "Boolean: No"
    assert data["attributes"][-1]["values"][0]["boolean"] is new_value
    assert boolean_attribute.values.count() == values_count
    product_variant_updated.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_update_variant_with_rich_text_attribute(
    product_variant_updated,
    permission_manage_products,
    product,
    product_type,
    staff_api_client,
    rich_text_attribute,
    warehouse,
):
    product_type.variant_attributes.add(rich_text_attribute)
    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "123"
    attr_id = graphene.Node.to_global_id("Attribute", rich_text_attribute.id)
    rich_text_attribute_value = rich_text_attribute.values.first()
    rich_text = json.dumps(rich_text_attribute_value.rich_text)
    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": attr_id, "richText": rich_text},
        ],
    }
    rich_text_attribute_value.slug = f"{variant.id}_{rich_text_attribute.id}"
    rich_text_attribute_value.save()
    values_count = rich_text_attribute.values.count()
    associate_attribute_values_to_instance(
        variant, rich_text_attribute, rich_text_attribute.values.first()
    )

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantUpdate"]
    variant.refresh_from_db()
    data = content["productVariant"]

    assert not content["errors"]
    assert data["sku"] == sku
    assert data["attributes"][-1]["attribute"]["slug"] == rich_text_attribute.slug
    assert data["attributes"][-1]["values"][0]["richText"] == rich_text
    assert rich_text_attribute.values.count() == values_count
    product_variant_updated.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_update_variant_with_plain_text_attribute(
    product_variant_updated,
    permission_manage_products,
    product,
    product_type,
    staff_api_client,
    plain_text_attribute,
    warehouse,
):
    # given
    product_type.variant_attributes.add(plain_text_attribute)
    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "123"
    attr_id = graphene.Node.to_global_id("Attribute", plain_text_attribute.id)
    plain_text_attribute_value = plain_text_attribute.values.first()
    text = plain_text_attribute_value.plain_text
    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": attr_id, "plainText": text},
        ],
    }
    plain_text_attribute_value.slug = f"{variant.id}_{plain_text_attribute.id}"
    plain_text_attribute_value.save()
    values_count = plain_text_attribute.values.count()
    associate_attribute_values_to_instance(
        variant, plain_text_attribute, plain_text_attribute.values.first()
    )

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)["data"]["productVariantUpdate"]
    variant.refresh_from_db()
    data = content["productVariant"]

    assert not content["errors"]
    assert data["sku"] == sku
    assert data["attributes"][-1]["attribute"]["slug"] == plain_text_attribute.slug
    assert data["attributes"][-1]["values"][0]["plainText"] == text
    assert plain_text_attribute.values.count() == values_count
    product_variant_updated.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_update_variant_with_plain_text_attribute_value_required(
    product_variant_updated,
    permission_manage_products,
    product,
    product_type,
    staff_api_client,
    plain_text_attribute,
    warehouse,
):
    # given
    product_type.variant_attributes.add(plain_text_attribute)
    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "123"
    attr_id = graphene.Node.to_global_id("Attribute", plain_text_attribute.id)
    plain_text_attribute_value = plain_text_attribute.values.first()
    text = plain_text_attribute_value.plain_text
    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": attr_id, "plainText": text},
        ],
    }
    plain_text_attribute_value.slug = f"{variant.id}_{plain_text_attribute.id}"
    plain_text_attribute_value.save()

    plain_text_attribute.value_required = True
    plain_text_attribute.save(update_fields=["value_required"])

    values_count = plain_text_attribute.values.count()
    associate_attribute_values_to_instance(
        variant, plain_text_attribute, plain_text_attribute.values.first()
    )

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)["data"]["productVariantUpdate"]
    variant.refresh_from_db()
    data = content["productVariant"]

    assert not content["errors"]
    assert data["sku"] == sku
    assert data["attributes"][-1]["attribute"]["slug"] == plain_text_attribute.slug
    assert data["attributes"][-1]["values"][0]["plainText"] == text
    assert plain_text_attribute.values.count() == values_count
    product_variant_updated.assert_called_once_with(product.variants.last())


@pytest.mark.parametrize("value", ["", "  ", None])
def test_update_variant_with_required_plain_text_attribute_no_value(
    value,
    permission_manage_products,
    product,
    product_type,
    staff_api_client,
    plain_text_attribute,
):
    # given
    product_type.variant_attributes.add(plain_text_attribute)
    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "123"
    attr_id = graphene.Node.to_global_id("Attribute", plain_text_attribute.id)

    plain_text_attribute_value = plain_text_attribute.values.first()
    plain_text_attribute_value.slug = f"{variant.id}_{plain_text_attribute.id}"
    plain_text_attribute_value.save()

    associate_attribute_values_to_instance(
        variant, plain_text_attribute, plain_text_attribute.values.first()
    )

    plain_text_attribute.value_required = True
    plain_text_attribute.save(update_fields=["value_required"])

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": attr_id, "plainText": value},
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)["data"]["productVariantUpdate"]
    variant.refresh_from_db()
    data = content["productVariant"]
    errors = content["errors"]

    assert not data
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_update_variant_with_date_attribute(
    product_variant_updated,
    permission_manage_products,
    product,
    product_type,
    date_attribute,
    warehouse,
    staff_api_client,
):
    product_type.variant_attributes.add(date_attribute)

    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "123"
    date_attribute_id = graphene.Node.to_global_id("Attribute", date_attribute.id)
    date_time_value = datetime(2025, 5, 5, 5, 5, 5, tzinfo=pytz.utc)
    date_value = date_time_value.date()
    date_values_count = date_attribute.values.count()

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": date_attribute_id, "date": date_value},
        ],
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantUpdate"]
    variant.refresh_from_db()
    data = content["productVariant"]
    expected_attributes_data = {
        "attribute": {"slug": "release-date"},
        "values": [
            {
                "id": ANY,
                "boolean": None,
                "file": None,
                "reference": None,
                "richText": None,
                "plainText": None,
                "dateTime": None,
                "date": str(date_value),
                "name": str(date_value),
                "slug": f"{variant.id}_{date_attribute.id}",
            }
        ],
    }

    assert not content["errors"]
    assert data["sku"] == sku
    assert date_values_count + 1 == date_attribute.values.count()
    assert expected_attributes_data in data["attributes"]
    product_variant_updated.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_update_variant_with_date_time_attribute(
    product_variant_updated,
    permission_manage_products,
    product,
    product_type,
    date_attribute,
    date_time_attribute,
    warehouse,
    staff_api_client,
):
    product_type.variant_attributes.add(date_time_attribute)

    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "123"
    date_time_attribute_id = graphene.Node.to_global_id(
        "Attribute", date_time_attribute.id
    )
    date_time_value = datetime(2025, 5, 5, 5, 5, 5, tzinfo=pytz.utc)
    date_time_values_count = date_time_attribute.values.count()

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": date_time_attribute_id, "dateTime": date_time_value},
        ],
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantUpdate"]
    variant.refresh_from_db()
    data = content["productVariant"]
    expected_attributes_data = {
        "attribute": {"slug": "release-date-time"},
        "values": [
            {
                "id": ANY,
                "boolean": None,
                "file": None,
                "reference": None,
                "richText": None,
                "plainText": None,
                "dateTime": date_time_value.isoformat(),
                "date": None,
                "name": str(date_time_value),
                "slug": f"{variant.id}_{date_time_attribute.id}",
            }
        ],
    }

    assert not content["errors"]
    assert data["sku"] == sku
    assert date_time_values_count + 1 == date_time_attribute.values.count()
    assert expected_attributes_data in data["attributes"]
    product_variant_updated.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_update_variant_with_numeric_attribute(
    product_variant_updated,
    permission_manage_products,
    product,
    product_type,
    staff_api_client,
    numeric_attribute,
    warehouse,
):
    product_type.variant_attributes.add(numeric_attribute)
    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "123"
    attr_id = graphene.Node.to_global_id("Attribute", numeric_attribute.id)
    attribute_value = numeric_attribute.values.first()
    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": attr_id, "values": []},
        ],
    }
    attribute_value.slug = f"{variant.id}_{numeric_attribute.id}"
    attribute_value.save()
    values_count = numeric_attribute.values.count()
    associate_attribute_values_to_instance(variant, numeric_attribute, attribute_value)

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantUpdate"]
    variant.refresh_from_db()
    data = content["productVariant"]

    assert not content["errors"]
    assert data["sku"] == sku
    assert data["attributes"][-1]["attribute"]["slug"] == numeric_attribute.slug
    assert not data["attributes"][-1]["values"]
    assert numeric_attribute.values.count() == values_count
    product_variant_updated.assert_called_once_with(product.variants.last())


def test_update_product_variant_with_new_attribute(
    staff_api_client,
    product_with_variant_with_two_attributes,
    color_attribute,
    size_attribute,
    permission_manage_products,
):
    product = product_with_variant_with_two_attributes
    variant = product.variants.first()
    sku = str(uuid4())[:12]
    assert not variant.sku == sku
    assert variant.attributes.first().values.first().slug == "red"
    assert variant.attributes.last().values.first().slug == "small"

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": color_attribute_id, "values": ["red"]},
            {"id": size_attribute_id, "values": ["big"]},
        ],
    }

    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_ATTRIBUTES,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    data = content["data"]["productVariantUpdate"]
    assert not data["errors"]
    variant.refresh_from_db()
    assert variant.sku == sku
    assert variant.attributes.first().values.first().slug == "red"
    assert variant.attributes.last().values.first().slug == "big"


def test_update_product_variant_clear_attributes(
    staff_api_client,
    product,
    permission_manage_products,
):
    variant = product.variants.first()
    sku = str(uuid4())[:12]
    assert not variant.sku == sku

    variant_attr = variant.attributes.first()
    attribute = variant_attr.assignment.attribute
    attribute.input_type = AttributeInputType.MULTISELECT
    attribute.value_required = False
    attribute_variant = attribute.attributevariant.get()
    attribute_variant.variant_selection = False
    attribute_variant.save(update_fields=["variant_selection"])
    attribute.save(update_fields=["value_required", "input_type"])

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.pk)

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": attribute_id, "values": []},
        ],
    }

    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_ATTRIBUTES,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    data = content["data"]["productVariantUpdate"]
    assert not data["errors"]
    variant.refresh_from_db()
    assert not data["productVariant"]["attributes"][0]["values"]
    with pytest.raises(variant_attr._meta.model.DoesNotExist):
        variant_attr.refresh_from_db()


def test_update_product_variant_with_duplicated_attribute(
    staff_api_client,
    product_with_variant_with_two_attributes,
    color_attribute,
    size_attribute,
    permission_manage_products,
):
    product = product_with_variant_with_two_attributes
    variant = product.variants.first()
    variant2 = product.variants.first()

    variant2.pk = None
    variant2.sku = str(uuid4())[:12]
    variant2.save()
    associate_attribute_values_to_instance(
        variant2, color_attribute, color_attribute.values.last()
    )
    associate_attribute_values_to_instance(
        variant2, size_attribute, size_attribute.values.last()
    )

    assert variant.attributes.first().values.first().slug == "red"
    assert variant.attributes.last().values.first().slug == "small"
    assert variant2.attributes.first().values.first().slug == "blue"
    assert variant2.attributes.last().values.first().slug == "big"

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)

    variables = {
        "id": variant_id,
        "attributes": [
            {"id": color_attribute_id, "values": ["blue"]},
            {"id": size_attribute_id, "values": ["big"]},
        ],
    }

    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_ATTRIBUTES,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    data = content["data"]["productVariantUpdate"]
    assert data["errors"][0] == {
        "field": "attributes",
        "code": ProductErrorCode.DUPLICATED_INPUT_ITEM.name,
        "message": ANY,
    }


def test_update_product_variant_with_current_file_attribute(
    staff_api_client,
    product_with_variant_with_file_attribute,
    file_attribute,
    permission_manage_products,
):
    product = product_with_variant_with_file_attribute
    variant = product.variants.first()
    sku = str(uuid4())[:12]
    assert not variant.sku == sku
    assert set(variant.attributes.first().values.values_list("slug", flat=True)) == {
        "test_filetxt"
    }
    second_value = file_attribute.values.last()

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    file_attribute_id = graphene.Node.to_global_id("Attribute", file_attribute.pk)

    variables = {
        "id": variant_id,
        "sku": sku,
        "price": 15,
        "attributes": [{"id": file_attribute_id, "file": second_value.file_url}],
    }

    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_ATTRIBUTES,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    data = content["data"]["productVariantUpdate"]
    assert not data["errors"]
    variant_data = data["productVariant"]
    assert variant_data
    assert variant_data["sku"] == sku
    assert len(variant_data["attributes"]) == 1
    assert variant_data["attributes"][0]["attribute"]["slug"] == file_attribute.slug
    assert len(variant_data["attributes"][0]["values"]) == 1
    assert (
        variant_data["attributes"][0]["values"][0]["slug"]
        == f"{slugify(second_value)}-2"
    )


def test_update_product_variant_with_duplicated_file_attribute(
    staff_api_client,
    product_with_variant_with_file_attribute,
    file_attribute,
    permission_manage_products,
):
    product = product_with_variant_with_file_attribute
    variant = product.variants.first()
    variant2 = product.variants.first()

    variant2.pk = None
    variant2.sku = str(uuid4())[:12]
    variant2.save()
    file_attr_value = file_attribute.values.last()
    associate_attribute_values_to_instance(variant2, file_attribute, file_attr_value)

    sku = str(uuid4())[:12]
    assert not variant.sku == sku

    assert set(variant.attributes.first().values.values_list("slug", flat=True)) == {
        "test_filetxt"
    }
    assert set(variant2.attributes.first().values.values_list("slug", flat=True)) == {
        "test_filejpeg"
    }

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    file_attribute_id = graphene.Node.to_global_id("Attribute", file_attribute.pk)

    variables = {
        "id": variant_id,
        "price": 15,
        "attributes": [{"id": file_attribute_id, "file": file_attr_value.file_url}],
        "sku": sku,
    }

    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_ATTRIBUTES,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    data = content["data"]["productVariantUpdate"]
    assert data["errors"][0] == {
        "field": "attributes",
        "code": ProductErrorCode.DUPLICATED_INPUT_ITEM.name,
        "message": ANY,
    }


def test_update_product_variant_with_file_attribute_new_value_is_not_created(
    staff_api_client,
    product_with_variant_with_file_attribute,
    file_attribute,
    permission_manage_products,
):
    product = product_with_variant_with_file_attribute
    variant = product.variants.first()
    sku = str(uuid4())[:12]
    assert not variant.sku == sku

    existing_value = file_attribute.values.first()
    assert variant.attributes.filter(
        assignment__attribute=file_attribute, values=existing_value
    ).exists()

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    file_attribute_id = graphene.Node.to_global_id("Attribute", file_attribute.pk)

    variables = {
        "id": variant_id,
        "sku": sku,
        "price": 15,
        "attributes": [{"id": file_attribute_id, "file": existing_value.file_url}],
    }

    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_ATTRIBUTES,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    data = content["data"]["productVariantUpdate"]
    assert not data["errors"]
    variant_data = data["productVariant"]
    assert variant_data
    assert variant_data["sku"] == sku
    assert len(variant_data["attributes"]) == 1
    assert variant_data["attributes"][0]["attribute"]["slug"] == file_attribute.slug
    assert len(variant_data["attributes"][0]["values"]) == 1
    value_data = variant_data["attributes"][0]["values"][0]
    assert value_data["slug"] == existing_value.slug
    assert value_data["name"] == existing_value.name
    assert (
        value_data["file"]["url"]
        == f"http://{TEST_SERVER_DOMAIN}/media/{existing_value.file_url}"
    )
    assert value_data["file"]["contentType"] == existing_value.content_type


def test_update_product_variant_with_page_reference_attribute(
    staff_api_client,
    product,
    page,
    product_type_page_reference_attribute,
    permission_manage_products,
):
    variant = product.variants.first()
    sku = str(uuid4())[:12]
    assert not variant.sku == sku

    product_type = product.product_type
    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(product_type_page_reference_attribute)

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.pk
    )
    reference = graphene.Node.to_global_id("Page", page.pk)

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [{"id": ref_attribute_id, "references": [reference]}],
    }

    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_ATTRIBUTES,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    data = content["data"]["productVariantUpdate"]
    assert not data["errors"]
    variant_data = data["productVariant"]
    assert variant_data
    assert variant_data["sku"] == sku
    assert len(variant_data["attributes"]) == 1
    assert (
        variant_data["attributes"][0]["attribute"]["slug"]
        == product_type_page_reference_attribute.slug
    )
    assert len(variant_data["attributes"][0]["values"]) == 1
    assert (
        variant_data["attributes"][0]["values"][0]["slug"] == f"{variant.pk}_{page.pk}"
    )
    assert variant_data["attributes"][0]["values"][0]["reference"] == reference


def test_update_product_variant_with_product_reference_attribute(
    staff_api_client,
    product_list,
    product_type_product_reference_attribute,
    permission_manage_products,
):
    product = product_list[0]
    product_ref = product_list[1]

    variant = product.variants.first()
    sku = str(uuid4())[:12]
    assert not variant.sku == sku

    product_type = product.product_type
    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(product_type_product_reference_attribute)

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.pk
    )
    reference = graphene.Node.to_global_id("Product", product_ref.pk)

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [{"id": ref_attribute_id, "references": [reference]}],
    }

    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_ATTRIBUTES,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    data = content["data"]["productVariantUpdate"]
    assert not data["errors"]
    variant_data = data["productVariant"]
    assert variant_data
    assert variant_data["sku"] == sku
    assert len(variant_data["attributes"]) == 1
    assert (
        variant_data["attributes"][0]["attribute"]["slug"]
        == product_type_product_reference_attribute.slug
    )
    assert len(variant_data["attributes"][0]["values"]) == 1
    assert (
        variant_data["attributes"][0]["values"][0]["slug"]
        == f"{variant.pk}_{product_ref.pk}"
    )
    assert variant_data["attributes"][0]["values"][0]["reference"] == reference


def test_update_product_variant_change_attribute_values_ordering(
    staff_api_client,
    variant,
    product_type_product_reference_attribute,
    permission_manage_products,
    product_list,
):
    # given
    product_type = variant.product.product_type
    product_type.variant_attributes.set([product_type_product_reference_attribute])
    sku = str(uuid4())[:12]

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.pk
    )

    attr_value_1 = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=product_list[0].name,
        slug=f"{variant.pk}_{product_list[0].pk}",
        reference_product=product_list[0],
    )
    attr_value_2 = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=product_list[1].name,
        slug=f"{variant.pk}_{product_list[1].pk}",
        reference_product=product_list[1],
    )
    attr_value_3 = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=product_list[2].name,
        slug=f"{variant.pk}_{product_list[2].pk}",
        reference_product=product_list[2],
    )

    associate_attribute_values_to_instance(
        variant,
        product_type_product_reference_attribute,
        attr_value_3,
        attr_value_2,
        attr_value_1,
    )

    assert list(
        variant.attributes.first().variantvalueassignment.values_list(
            "value_id", flat=True
        )
    ) == [attr_value_3.pk, attr_value_2.pk, attr_value_1.pk]

    new_ref_order = [product_list[1], product_list[0], product_list[2]]
    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {
                "id": attribute_id,
                "references": [
                    graphene.Node.to_global_id("Product", ref.pk)
                    for ref in new_ref_order
                ],
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_ATTRIBUTES,
        variables,
        permissions=[permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]
    assert data["errors"] == []

    attributes = data["productVariant"]["attributes"]

    assert len(attributes) == 1
    values = attributes[0]["values"]
    assert len(values) == 3
    assert [value["id"] for value in values] == [
        graphene.Node.to_global_id("AttributeValue", val.pk)
        for val in [attr_value_2, attr_value_1, attr_value_3]
    ]
    variant.refresh_from_db()
    assert list(
        variant.attributes.first().variantvalueassignment.values_list(
            "value_id", flat=True
        )
    ) == [attr_value_2.pk, attr_value_1.pk, attr_value_3.pk]


@pytest.mark.parametrize(
    "values, message, code",
    (
        (["one", "two"], "Attribute must take only one value.", "INVALID"),
        (["   "], "Attribute values cannot be blank.", "REQUIRED"),
    ),
)
def test_update_product_variant_requires_values(
    staff_api_client,
    variant,
    product_type,
    permission_manage_products,
    values,
    message,
    code,
):
    """Ensures updating a variant with invalid values raise an error.

    - Blank value
    - More than one value
    """

    sku = "updated"

    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    attr_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().id
    )

    variables = {
        "id": variant_id,
        "attributes": [{"id": attr_id, "values": values}],
        "sku": sku,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    assert (
        len(content["data"]["productVariantUpdate"]["errors"]) == 1
    ), f"expected: {message}"
    assert content["data"]["productVariantUpdate"]["errors"][0] == {
        "field": "attributes",
        "message": message,
        "code": code,
    }
    assert not variant.product.variants.filter(sku=sku).exists()


def test_update_product_variant_requires_attr_value_when_is_required(
    staff_api_client,
    variant,
    product_type,
    permission_manage_products,
):
    sku = "updated"

    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    attribute = product_type.variant_attributes.first()
    attribute.value_required = True
    attribute.save(update_fields=["value_required"])

    attr_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().id
    )

    variables = {
        "id": variant_id,
        "attributes": [{"id": attr_id, "values": []}],
        "sku": sku,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    assert len(content["data"]["productVariantUpdate"]["errors"]) == 1
    assert content["data"]["productVariantUpdate"]["errors"][0] == {
        "field": "attributes",
        "message": "Attribute expects a value but none were given.",
        "code": "REQUIRED",
    }
    assert not variant.product.variants.filter(sku=sku).exists()


def test_update_product_variant_with_price_does_not_raise_price_validation_error(
    staff_api_client, variant, size_attribute, permission_manage_products
):
    mutation = """
    mutation updateVariant ($id: ID!, $attributes: [AttributeValueInput!]) {
        productVariantUpdate(
            id: $id,
            input: {
            attributes: $attributes,
        }) {
            productVariant {
                id
            }
            errors {
                field
                code
            }
        }
    }
    """
    # given a product variant and an attribute
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)

    # when running the updateVariant mutation without price input field
    variables = {
        "id": variant_id,
        "attributes": [{"id": attribute_id, "values": ["S"]}],
    }
    response = staff_api_client.post_graphql(
        mutation, variables, permissions=[permission_manage_products]
    )

    # then mutation passes without validation errors
    content = get_graphql_content(response)
    assert not content["data"]["productVariantUpdate"]["errors"]


QUERY_UPDATE_VARIANT_PREORDER = """
    mutation updateVariant (
        $id: ID!,
        $sku: String!,
        $preorder: PreorderSettingsInput) {
            productVariantUpdate(
                id: $id,
                input: {
                    sku: $sku,
                    preorder: $preorder,
                }) {
                productVariant {
                    sku
                    preorder {
                        globalThreshold
                        endDate
                    }
                }
            }
        }
"""


def test_update_product_variant_change_preorder_data(
    staff_api_client,
    permission_manage_products,
    preorder_variant_global_threshold,
):
    variant = preorder_variant_global_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "test sku"

    new_global_threshold = variant.preorder_global_threshold + 5
    assert variant.preorder_end_date is None
    new_preorder_end_date = (
        (datetime.now() + timedelta(days=3))
        .astimezone()
        .replace(microsecond=0)
        .isoformat()
    )
    variables = {
        "id": variant_id,
        "sku": sku,
        "preorder": {
            "globalThreshold": new_global_threshold,
            "endDate": new_preorder_end_date,
        },
    }

    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_PREORDER,
        variables,
        permissions=[permission_manage_products],
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantUpdate"]["productVariant"]

    assert data["sku"] == sku
    assert data["preorder"]["globalThreshold"] == new_global_threshold
    assert data["preorder"]["endDate"] == new_preorder_end_date


def test_update_product_variant_can_not_turn_off_preorder(
    staff_api_client,
    permission_manage_products,
    preorder_variant_global_threshold,
):
    """Passing None with `preorder` field can not turn off preorder,
    it could be done only with ProductVariantPreorderDeactivate mutation."""
    variant = preorder_variant_global_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "test sku"

    variables = {"id": variant_id, "sku": sku, "preorder": None}

    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_PREORDER,
        variables,
        permissions=[permission_manage_products],
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantUpdate"]["productVariant"]

    assert data["sku"] == sku
    assert data["preorder"]["globalThreshold"] == variant.preorder_global_threshold
    assert data["preorder"]["endDate"] is None


DELETE_VARIANT_MUTATION = """
    mutation variantDelete($id: ID!) {
        productVariantDelete(id: $id) {
            productVariant {
                sku
                id
            }
            }
        }
"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_deleted")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_variant(
    mocked_recalculate_orders_task,
    product_variant_deleted_webhook_mock,
    staff_api_client,
    product,
    permission_manage_products,
):
    query = DELETE_VARIANT_MUTATION
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variant_sku = variant.sku
    variables = {"id": variant_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantDelete"]

    product_variant_deleted_webhook_mock.assert_called_once_with(variant)
    assert data["productVariant"]["sku"] == variant_sku
    with pytest.raises(variant._meta.model.DoesNotExist):
        variant.refresh_from_db()
    mocked_recalculate_orders_task.assert_not_called()


def test_delete_variant_remove_checkout_lines(
    staff_api_client,
    checkout_with_items,
    permission_manage_products,
):
    query = DELETE_VARIANT_MUTATION
    line = checkout_with_items.lines.first()
    variant = line.variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantDelete"]

    assert data["productVariant"]["sku"] == variant.sku
    with pytest.raises(variant._meta.model.DoesNotExist):
        variant.refresh_from_db()
    with pytest.raises(line._meta.model.DoesNotExist):
        line.refresh_from_db()


@patch("saleor.product.signals.delete_from_storage_task.delay")
@patch("saleor.plugins.manager.PluginsManager.product_variant_deleted")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_variant_with_image(
    mocked_recalculate_orders_task,
    product_variant_deleted_webhook_mock,
    delete_from_storage_task_mock,
    staff_api_client,
    variant_with_image,
    permission_manage_products,
    media_root,
):
    """Ensure deleting variant doesn't delete linked product image."""

    query = DELETE_VARIANT_MUTATION
    variant = variant_with_image

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantDelete"]

    product_variant_deleted_webhook_mock.assert_called_once_with(variant)
    assert data["productVariant"]["sku"] == variant.sku
    with pytest.raises(variant._meta.model.DoesNotExist):
        variant.refresh_from_db()
    mocked_recalculate_orders_task.assert_not_called()
    delete_from_storage_task_mock.assert_not_called()


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_variant_in_draft_order(
    mocked_recalculate_orders_task,
    staff_api_client,
    order_line,
    permission_manage_products,
    order_list,
    channel_USD,
):
    query = DELETE_VARIANT_MUTATION

    draft_order = order_line.order
    draft_order.status = OrderStatus.DRAFT
    draft_order.save(update_fields=["status"])

    variant = order_line.variant
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}

    product = variant.product
    net = variant.get_price(product, [], channel_USD, variant_channel_listing, None)
    gross = Money(amount=net.amount, currency=net.currency)
    order_not_draft = order_list[-1]
    unit_price = TaxedMoney(net=net, gross=gross)
    quantity = 3
    order_line_not_in_draft = OrderLine.objects.create(
        variant=variant,
        order=order_not_draft,
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        unit_price=unit_price,
        total_price=unit_price * quantity,
        quantity=quantity,
    )
    order_line_not_in_draft_pk = order_line_not_in_draft.pk
    second_draft_order = order_list[0]
    second_draft_order.status = OrderStatus.DRAFT
    second_draft_order.save(update_fields=["status"])
    OrderLine.objects.create(
        variant=variant,
        order=second_draft_order,
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        unit_price=unit_price,
        total_price=unit_price * quantity,
        quantity=quantity,
    )
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    content = get_graphql_content(response)
    data = content["data"]["productVariantDelete"]
    assert data["productVariant"]["sku"] == variant.sku
    with pytest.raises(order_line._meta.model.DoesNotExist):
        order_line.refresh_from_db()

    assert OrderLine.objects.filter(pk=order_line_not_in_draft_pk).exists()
    expected_call_args = sorted([second_draft_order.id, draft_order.id])
    result_call_args = sorted(mocked_recalculate_orders_task.mock_calls[0].args[0])

    assert result_call_args == expected_call_args

    events = OrderEvent.objects.filter(type=OrderEvents.ORDER_LINE_VARIANT_DELETED)
    assert events
    assert {event.order for event in events} == {draft_order, second_draft_order}
    assert {event.user for event in events} == {staff_api_client.user}
    expected_params = [
        {
            "item": str(line),
            "line_pk": line.pk,
            "quantity": line.quantity,
        }
        for line in draft_order.lines.all()
    ]
    for param in expected_params:
        assert param in events.get(order=draft_order).parameters
    expected_params = [
        {
            "item": str(line),
            "line_pk": line.pk,
            "quantity": line.quantity,
        }
        for line in second_draft_order.lines.all()
    ]
    for param in expected_params:
        assert param in events.get(order=second_draft_order).parameters


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_default_variant(
    mocked_recalculate_orders_task,
    staff_api_client,
    product_with_two_variants,
    permission_manage_products,
):
    # given
    query = DELETE_VARIANT_MUTATION
    product = product_with_two_variants

    default_variant = product.variants.first()
    second_variant = product.variants.last()

    product.default_variant = default_variant
    product.save(update_fields=["default_variant"])

    assert second_variant.pk != default_variant.pk

    variant_id = graphene.Node.to_global_id("ProductVariant", default_variant.pk)
    variables = {"id": variant_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantDelete"]
    assert data["productVariant"]["sku"] == default_variant.sku
    with pytest.raises(default_variant._meta.model.DoesNotExist):
        default_variant.refresh_from_db()

    product.refresh_from_db()
    assert product.default_variant.pk == second_variant.pk
    mocked_recalculate_orders_task.assert_not_called()


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_not_default_variant_left_default_variant_unchanged(
    mocked_recalculate_orders_task,
    staff_api_client,
    product_with_two_variants,
    permission_manage_products,
):
    # given
    query = DELETE_VARIANT_MUTATION
    product = product_with_two_variants

    default_variant = product.variants.first()
    second_variant = product.variants.last()

    product.default_variant = default_variant
    product.save(update_fields=["default_variant"])

    assert second_variant.pk != default_variant.pk

    variant_id = graphene.Node.to_global_id("ProductVariant", second_variant.pk)
    variables = {"id": variant_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantDelete"]
    assert data["productVariant"]["sku"] == second_variant.sku
    with pytest.raises(second_variant._meta.model.DoesNotExist):
        second_variant.refresh_from_db()

    product.refresh_from_db()
    assert product.default_variant.pk == default_variant.pk
    mocked_recalculate_orders_task.assert_not_called()


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_default_all_product_variant_left_product_default_variant_unset(
    mocked_recalculate_orders_task,
    staff_api_client,
    product,
    permission_manage_products,
):
    # given
    query = DELETE_VARIANT_MUTATION

    default_variant = product.variants.first()

    product.default_variant = default_variant
    product.save(update_fields=["default_variant"])

    assert product.variants.count() == 1

    variant_id = graphene.Node.to_global_id("ProductVariant", default_variant.pk)
    variables = {"id": variant_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantDelete"]
    assert data["productVariant"]["sku"] == default_variant.sku
    with pytest.raises(default_variant._meta.model.DoesNotExist):
        default_variant.refresh_from_db()

    product.refresh_from_db()
    assert not product.default_variant
    mocked_recalculate_orders_task.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_deleted")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_variant_delete_product_channel_listing_without_available_channel(
    mocked_recalculate_orders_task,
    product_variant_deleted_webhook_mock,
    staff_api_client,
    product,
    permission_manage_products,
):
    """Ensure that when the last available variant for channel is removed,
    the corresponging product channel listings will be removed too."""
    # given
    query = DELETE_VARIANT_MUTATION
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variant_sku = variant.sku
    variables = {"id": variant_id}

    # second variant not available
    ProductVariant.objects.create(product=product, sku="not-available-variant")

    assert product.channel_listings.count() == 1

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantDelete"]

    product_variant_deleted_webhook_mock.assert_called_once_with(variant)
    assert data["productVariant"]["sku"] == variant_sku
    with pytest.raises(variant._meta.model.DoesNotExist):
        variant.refresh_from_db()
    mocked_recalculate_orders_task.assert_not_called()
    product.refresh_from_db()
    assert product.channel_listings.count() == 0


@patch("saleor.plugins.manager.PluginsManager.product_variant_deleted")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_variant_delete_product_channel_listing_not_deleted(
    mocked_recalculate_orders_task,
    product_variant_deleted_webhook_mock,
    staff_api_client,
    product_with_two_variants,
    permission_manage_products,
):
    """Ensure that any other available variant for channel exist,
    the corresponging product channel listings will be not removed."""
    # given
    query = DELETE_VARIANT_MUTATION
    product = product_with_two_variants
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variant_sku = variant.sku
    variables = {"id": variant_id}

    product_channel_listing_count = product.channel_listings.count()

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantDelete"]

    product_variant_deleted_webhook_mock.assert_called_once_with(variant)
    assert data["productVariant"]["sku"] == variant_sku
    with pytest.raises(variant._meta.model.DoesNotExist):
        variant.refresh_from_db()
    mocked_recalculate_orders_task.assert_not_called()
    product.refresh_from_db()
    assert product.channel_listings.count() == product_channel_listing_count


def _fetch_all_variants(client, variables={}, permissions=None):
    query = """
        query fetchAllVariants($channel: String) {
            productVariants(first: 10, channel: $channel) {
                totalCount
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """
    response = client.post_graphql(
        query, variables, permissions=permissions, check_no_permissions=False
    )
    content = get_graphql_content(response)
    return content["data"]["productVariants"]


def test_fetch_all_variants_staff_user(
    staff_api_client, unavailable_product_with_variant, permission_manage_products
):
    variant = unavailable_product_with_variant.variants.first()
    data = _fetch_all_variants(
        staff_api_client, permissions=[permission_manage_products]
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    assert data["totalCount"] == 1
    assert data["edges"][0]["node"]["id"] == variant_id


def test_fetch_all_variants_staff_user_with_channel(
    staff_api_client,
    product_list_with_variants_many_channel,
    permission_manage_products,
    channel_PLN,
):
    variables = {"channel": channel_PLN.slug}
    data = _fetch_all_variants(
        staff_api_client, variables, permissions=[permission_manage_products]
    )
    assert data["totalCount"] == 2


def test_fetch_all_variants_staff_user_without_channel(
    staff_api_client,
    product_list_with_variants_many_channel,
    permission_manage_products,
):
    data = _fetch_all_variants(
        staff_api_client, permissions=[permission_manage_products]
    )
    assert data["totalCount"] == 3


def test_fetch_all_variants_customer(
    user_api_client, unavailable_product_with_variant, channel_USD
):
    data = _fetch_all_variants(user_api_client, variables={"channel": channel_USD.slug})
    assert data["totalCount"] == 0


def test_fetch_all_variants_anonymous_user(
    api_client, unavailable_product_with_variant, channel_USD
):
    data = _fetch_all_variants(api_client, variables={"channel": channel_USD.slug})
    assert data["totalCount"] == 0


def test_fetch_all_variants_without_sku_staff_user(
    staff_api_client, product, permission_manage_products
):
    variant = product.variants.first()
    variant.sku = None
    variant.save()

    data = _fetch_all_variants(
        staff_api_client, permissions=[permission_manage_products]
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    assert data["totalCount"] == 1
    assert data["edges"][0]["node"]["id"] == variant_id


def test_fetch_all_variants_without_sku_staff_user_with_channel(
    staff_api_client,
    product,
    permission_manage_products,
    channel_USD,
):
    variant = product.variants.first()
    variant.sku = None
    variant.save()

    variables = {"channel": channel_USD.slug}
    data = _fetch_all_variants(
        staff_api_client, variables, permissions=[permission_manage_products]
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    assert data["totalCount"] == 1
    assert data["edges"][0]["node"]["id"] == variant_id


def test_fetch_all_variants_without_sku_as_customer_with_channel(
    user_api_client, product, channel_USD
):
    variant = product.variants.first()
    variant.sku = None
    variant.save()

    ProductVariant.objects.update(sku=None)
    data = _fetch_all_variants(user_api_client, variables={"channel": channel_USD.slug})
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    assert data["totalCount"] == 1
    assert data["edges"][0]["node"]["id"] == variant_id


def test_fetch_all_variants_without_sku_as_anonymous_user_with_channel(
    api_client, product, channel_USD
):
    variant = product.variants.first()
    variant.sku = None
    variant.save()

    ProductVariant.objects.update(sku=None)
    data = _fetch_all_variants(api_client, variables={"channel": channel_USD.slug})
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    assert data["totalCount"] == 1
    assert data["edges"][0]["node"]["id"] == variant_id


QUERY_PRODUCT_VARIANTS_BY_IDS = """
    query getProductVariants($ids: [ID!], $channel: String) {
        productVariants(ids: $ids, first: 1, channel: $channel) {
            edges {
                node {
                    id
                }
            }
        }
    }
"""


def test_product_variants_by_ids(user_api_client, variant, channel_USD):
    query = QUERY_PRODUCT_VARIANTS_BY_IDS
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert data["edges"][0]["node"]["id"] == variant_id
    assert len(data["edges"]) == 1


def test_product_variants_by_invalid_ids(user_api_client, variant, channel_USD):
    query = QUERY_PRODUCT_VARIANTS_BY_IDS
    variant_id = "cbs"

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {variant_id}."
    assert content["data"]["productVariants"] is None


def test_product_variants_by_ids_that_do_not_exist(
    user_api_client, variant, channel_USD
):
    query = QUERY_PRODUCT_VARIANTS_BY_IDS
    variant_id = graphene.Node.to_global_id("Order", -1)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["productVariants"]["edges"] == []


def test_product_variants_visible_in_listings_by_customer(
    user_api_client, product_list, channel_USD
):
    # given
    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    # when
    data = _fetch_all_variants(user_api_client, variables={"channel": channel_USD.slug})

    assert data["totalCount"] == product_count - 1


def test_product_variants_visible_in_listings_by_staff_without_manage_products(
    staff_api_client, product_list, channel_USD
):
    # given
    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    # when
    data = _fetch_all_variants(
        staff_api_client, variables={"channel": channel_USD.slug}
    )

    assert data["totalCount"] == product_count - 1  # invisible doesn't count


def test_product_variants_visible_in_listings_by_staff_with_perm(
    staff_api_client, product_list, permission_manage_products, channel_USD
):
    # given
    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    # when
    data = _fetch_all_variants(
        staff_api_client,
        variables={"channel": channel_USD.slug},
        permissions=[permission_manage_products],
    )

    assert data["totalCount"] == product_count


def test_product_variants_visible_in_listings_by_app_without_manage_products(
    app_api_client, product_list, channel_USD
):
    # given
    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    # when
    data = _fetch_all_variants(app_api_client, variables={"channel": channel_USD.slug})

    assert data["totalCount"] == product_count - 1  # invisible doesn't count


def test_product_variants_visible_in_listings_by_app_with_perm(
    app_api_client, product_list, permission_manage_products, channel_USD
):
    # given
    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    # when
    data = _fetch_all_variants(
        app_api_client,
        variables={"channel": channel_USD.slug},
        permissions=[permission_manage_products],
    )

    assert data["totalCount"] == product_count


def _fetch_variant(client, variant, channel_slug=None, permissions=None):
    query = """
    query ProductVariantDetails($variantId: ID!, $channel: String) {
        productVariant(id: $variantId, channel: $channel) {
            id
            product {
                id
            }
        }
    }
    """
    variables = {"variantId": graphene.Node.to_global_id("ProductVariant", variant.id)}
    if channel_slug:
        variables["channel"] = channel_slug
    response = client.post_graphql(
        query, variables, permissions=permissions, check_no_permissions=False
    )
    content = get_graphql_content(response)
    return content["data"]["productVariant"]


def test_fetch_unpublished_variant_staff_user(
    staff_api_client, unavailable_product_with_variant, permission_manage_products
):
    variant = unavailable_product_with_variant.variants.first()
    data = _fetch_variant(
        staff_api_client,
        variant,
        permissions=[permission_manage_products],
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    product_id = graphene.Node.to_global_id(
        "Product", unavailable_product_with_variant.pk
    )

    assert data["id"] == variant_id
    assert data["product"]["id"] == product_id


def test_fetch_unpublished_variant_customer(
    user_api_client, unavailable_product_with_variant, channel_USD
):
    variant = unavailable_product_with_variant.variants.first()
    data = _fetch_variant(user_api_client, variant, channel_slug=channel_USD.slug)
    assert data is None


def test_fetch_unpublished_variant_anonymous_user(
    api_client, unavailable_product_with_variant, channel_USD
):
    variant = unavailable_product_with_variant.variants.first()
    data = _fetch_variant(api_client, variant, channel_slug=channel_USD.slug)
    assert data is None


def test_fetch_variant_without_sku_staff_user(
    staff_api_client, product, variant, permission_manage_products
):
    variant.sku = None
    variant.save()

    data = _fetch_variant(
        staff_api_client,
        variant,
        permissions=[permission_manage_products],
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    product_id = graphene.Node.to_global_id("Product", product.pk)

    assert data["id"] == variant_id
    assert data["product"]["id"] == product_id


def test_fetch_variant_without_sku_customer(
    user_api_client, product, variant, channel_USD
):
    variant.sku = None
    variant.save()

    data = _fetch_variant(
        user_api_client,
        variant,
        channel_slug=channel_USD.slug,
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    product_id = graphene.Node.to_global_id("Product", product.pk)

    assert data["id"] == variant_id
    assert data["product"]["id"] == product_id


def test_fetch_variant_without_sku_anonymous(api_client, product, variant, channel_USD):
    variant.sku = None
    variant.save()

    data = _fetch_variant(
        api_client,
        variant,
        channel_slug=channel_USD.slug,
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    product_id = graphene.Node.to_global_id("Product", product.pk)

    assert data["id"] == variant_id
    assert data["product"]["id"] == product_id


PRODUCT_VARIANT_BULK_CREATE_MUTATION = """
    mutation ProductVariantBulkCreate(
        $variants: [ProductVariantBulkCreateInput!]!, $productId: ID!
    ) {
        productVariantBulkCreate(variants: $variants, product: $productId) {
            errors {
                field
                message
                code
                index
                warehouses
                channels
            }
            productVariants{
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
            count
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
def test_product_variant_bulk_create_by_attribute_id(
    product_variant_created_webhook_mock,
    staff_api_client,
    product,
    size_attribute,
    permission_manage_products,
):
    product_variant_count = ProductVariant.objects.count()
    attribute_value_count = size_attribute.values.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribut_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    attribute_value = size_attribute.values.last()
    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [{"id": attribut_id, "values": [attribute_value.name]}],
        }
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantBulkCreate"]

    assert not data["errors"]
    assert data["count"] == 1
    assert data["productVariants"][0]["name"] == attribute_value.name
    assert product_variant_count + 1 == ProductVariant.objects.count()
    assert attribute_value_count == size_attribute.values.count()
    product_variant = ProductVariant.objects.get(sku=sku)
    product.refresh_from_db()
    assert product.default_variant == product_variant
    assert product_variant_created_webhook_mock.call_count == data["count"]


def test_product_variant_bulk_create_with_swatch_attribute(
    staff_api_client, product, swatch_attribute, permission_manage_products
):
    product_variant_count = ProductVariant.objects.count()
    product.product_type.variant_attributes.set(
        [swatch_attribute], through_defaults={"variant_selection": True}
    )
    attribute_value_count = swatch_attribute.values.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", swatch_attribute.pk)
    attribute_value_1 = swatch_attribute.values.first()
    attribute_value_2 = swatch_attribute.values.last()
    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [{"id": attribute_id, "values": [attribute_value_1.name]}],
        },
        {
            "sku": sku + "a",
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [{"id": attribute_id, "values": [attribute_value_2.name]}],
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert not data["errors"]
    assert data["count"] == 2
    assert {variant["name"] for variant in data["productVariants"]} == {
        attribute_value_1.name,
        attribute_value_2.name,
    }
    assert product_variant_count + 2 == ProductVariant.objects.count()
    assert attribute_value_count == swatch_attribute.values.count()
    product_variant = ProductVariant.objects.get(sku=sku)
    product.refresh_from_db()
    assert product.default_variant == product_variant


def test_product_variant_bulk_create_only_not_variant_selection_attributes(
    staff_api_client, product, size_attribute, permission_manage_products
):
    """Ensure that sku is set as variant name when only variant selection attributes
    are assigned.
    """
    product_variant_count = ProductVariant.objects.count()
    attribute_value_count = size_attribute.values.count()

    size_attribute.input_type = AttributeInputType.MULTISELECT
    variant_attribute = size_attribute.attributevariant.get()
    variant_attribute.variant_selection = False
    variant_attribute.save(update_fields=["variant_selection"])

    size_attribute.save(update_fields=["input_type"])

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribut_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)

    attribute_value = size_attribute.values.last()
    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [{"id": attribut_id, "values": [attribute_value.name]}],
        }
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert not data["errors"]
    assert data["count"] == 1
    assert data["productVariants"][0]["name"] == sku
    assert product_variant_count + 1 == ProductVariant.objects.count()
    assert attribute_value_count == size_attribute.values.count()
    product_variant = ProductVariant.objects.get(sku=sku)
    product.refresh_from_db()
    assert product.default_variant == product_variant


def test_product_variant_bulk_create_empty_attribute(
    staff_api_client, product, size_attribute, permission_manage_products
):
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variants = [{"sku": str(uuid4())[:12], "attributes": []}]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert not data["errors"]
    assert data["count"] == 1
    product.refresh_from_db()
    assert product_variant_count + 1 == ProductVariant.objects.count()


def test_product_variant_bulk_create_with_new_attribute_value(
    staff_api_client,
    product,
    size_attribute,
    permission_manage_products,
    boolean_attribute,
):
    product_variant_count = ProductVariant.objects.count()
    size_attribute_value_count = size_attribute.values.count()
    boolean_attribute_value_count = boolean_attribute.values.count()
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    boolean_attribute_id = graphene.Node.to_global_id("Attribute", boolean_attribute.pk)
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_value = size_attribute.values.last()
    variants = [
        {
            "sku": str(uuid4())[:12],
            "attributes": [
                {"id": size_attribute_id, "values": [attribute_value.name]},
                {"id": boolean_attribute_id, "boolean": None},
            ],
        },
        {
            "sku": str(uuid4())[:12],
            "attributes": [
                {"id": size_attribute_id, "values": ["Test-attribute"]},
                {"id": boolean_attribute_id, "boolean": True},
            ],
        },
    ]

    product.product_type.variant_attributes.add(boolean_attribute)

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert not data["errors"]
    assert data["count"] == 2
    assert product_variant_count + 2 == ProductVariant.objects.count()
    assert size_attribute_value_count + 1 == size_attribute.values.count()
    assert boolean_attribute_value_count == boolean_attribute.values.count()


def test_product_variant_bulk_create_variant_selection_and_other_attributes(
    staff_api_client,
    product,
    size_attribute,
    file_attribute,
    permission_manage_products,
):
    """Ensure that only values for variant selection attributes are required."""
    product_type = product.product_type
    product_type.variant_attributes.add(file_attribute)

    product_variant_count = ProductVariant.objects.count()
    attribute_value_count = size_attribute.values.count()

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)

    attribute_value = size_attribute.values.last()
    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [{"id": attribute_id, "values": [attribute_value.name]}],
        }
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert not data["errors"]
    assert data["count"] == 1
    assert product_variant_count + 1 == ProductVariant.objects.count()
    assert attribute_value_count == size_attribute.values.count()
    product_variant = ProductVariant.objects.get(sku=sku)
    product.refresh_from_db()
    assert product.default_variant == product_variant


def test_product_variant_bulk_create_stocks_input(
    staff_api_client, product, permission_manage_products, warehouses, size_attribute
):
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_value_count = size_attribute.values.count()
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    attribute_value = size_attribute.values.last()
    variants = [
        {
            "sku": str(uuid4())[:12],
            "stocks": [
                {
                    "quantity": 10,
                    "warehouse": graphene.Node.to_global_id(
                        "Warehouse", warehouses[0].pk
                    ),
                }
            ],
            "attributes": [{"id": size_attribute_id, "values": [attribute_value.name]}],
        },
        {
            "sku": str(uuid4())[:12],
            "attributes": [{"id": size_attribute_id, "values": ["Test-attribute"]}],
            "stocks": [
                {
                    "quantity": 15,
                    "warehouse": graphene.Node.to_global_id(
                        "Warehouse", warehouses[0].pk
                    ),
                },
                {
                    "quantity": 15,
                    "warehouse": graphene.Node.to_global_id(
                        "Warehouse", warehouses[1].pk
                    ),
                },
            ],
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert not data["errors"]
    assert data["count"] == 2
    assert product_variant_count + 2 == ProductVariant.objects.count()
    assert attribute_value_count + 1 == size_attribute.values.count()

    expected_result = {
        variants[0]["sku"]: {
            "sku": variants[0]["sku"],
            "stocks": [
                {
                    "warehouse": {"slug": warehouses[0].slug},
                    "quantity": variants[0]["stocks"][0]["quantity"],
                }
            ],
        },
        variants[1]["sku"]: {
            "sku": variants[1]["sku"],
            "stocks": [
                {
                    "warehouse": {"slug": warehouses[0].slug},
                    "quantity": variants[1]["stocks"][0]["quantity"],
                },
                {
                    "warehouse": {"slug": warehouses[1].slug},
                    "quantity": variants[1]["stocks"][1]["quantity"],
                },
            ],
        },
    }
    for variant_data in data["productVariants"]:
        variant_data.pop("id")
        assert variant_data["sku"] in expected_result
        expected_variant = expected_result[variant_data["sku"]]
        expected_stocks = expected_variant["stocks"]
        assert all([stock in expected_stocks for stock in variant_data["stocks"]])


def test_product_variant_bulk_create_duplicated_warehouses(
    staff_api_client, product, permission_manage_products, warehouses, size_attribute
):
    product_id = graphene.Node.to_global_id("Product", product.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    attribute_value = size_attribute.values.last()
    warehouse1_id = graphene.Node.to_global_id("Warehouse", warehouses[0].pk)
    variants = [
        {
            "sku": str(uuid4())[:12],
            "stocks": [
                {
                    "quantity": 10,
                    "warehouse": graphene.Node.to_global_id(
                        "Warehouse", warehouses[1].pk
                    ),
                }
            ],
            "attributes": [{"id": size_attribute_id, "values": [attribute_value.name]}],
        },
        {
            "sku": str(uuid4())[:12],
            "attributes": [{"id": size_attribute_id, "values": ["Test-attribute"]}],
            "stocks": [
                {"quantity": 15, "warehouse": warehouse1_id},
                {"quantity": 15, "warehouse": warehouse1_id},
            ],
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    errors = data["errors"]

    assert not data["productVariants"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "stocks"
    assert error["index"] == 1
    assert error["code"] == ProductErrorCode.DUPLICATED_INPUT_ITEM.name
    assert error["warehouses"] == [warehouse1_id]


def test_product_variant_bulk_create_channel_listings_input(
    staff_api_client,
    product_available_in_many_channels,
    permission_manage_products,
    warehouses,
    size_attribute,
    channel_USD,
    channel_PLN,
):
    product = product_available_in_many_channels
    ProductChannelListing.objects.filter(product=product, channel=channel_PLN).update(
        is_published=False
    )
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_value_count = size_attribute.values.count()
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    attribute_value = size_attribute.values.last()
    variants = [
        {
            "sku": str(uuid4())[:12],
            "channelListings": [
                {
                    "price": 10.0,
                    "costPrice": 11.0,
                    "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                }
            ],
            "attributes": [{"id": size_attribute_id, "values": [attribute_value.name]}],
        },
        {
            "sku": str(uuid4())[:12],
            "attributes": [{"id": size_attribute_id, "values": ["Test-attribute"]}],
            "channelListings": [
                {
                    "price": 15.0,
                    "costPrice": 16.0,
                    "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                },
                {
                    "price": 12.0,
                    "costPrice": 13.0,
                    "channelId": graphene.Node.to_global_id("Channel", channel_PLN.pk),
                },
            ],
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert not data["errors"]
    assert data["count"] == 2
    assert product_variant_count + 2 == ProductVariant.objects.count()
    assert attribute_value_count + 1 == size_attribute.values.count()

    expected_result = {
        variants[0]["sku"]: {
            "sku": variants[0]["sku"],
            "channelListings": [
                {
                    "channel": {"slug": channel_USD.slug},
                    "price": {
                        "amount": variants[0]["channelListings"][0]["price"],
                        "currency": channel_USD.currency_code,
                    },
                    "costPrice": {
                        "amount": variants[0]["channelListings"][0]["costPrice"],
                        "currency": channel_USD.currency_code,
                    },
                    "preorderThreshold": {"quantity": None},
                }
            ],
        },
        variants[1]["sku"]: {
            "sku": variants[1]["sku"],
            "channelListings": [
                {
                    "channel": {"slug": channel_USD.slug},
                    "price": {
                        "amount": variants[1]["channelListings"][0]["price"],
                        "currency": channel_USD.currency_code,
                    },
                    "costPrice": {
                        "amount": variants[1]["channelListings"][0]["costPrice"],
                        "currency": channel_USD.currency_code,
                    },
                    "preorderThreshold": {"quantity": None},
                },
                {
                    "channel": {"slug": channel_PLN.slug},
                    "price": {
                        "amount": variants[1]["channelListings"][1]["price"],
                        "currency": channel_PLN.currency_code,
                    },
                    "costPrice": {
                        "amount": variants[1]["channelListings"][1]["costPrice"],
                        "currency": channel_PLN.currency_code,
                    },
                    "preorderThreshold": {"quantity": None},
                },
            ],
        },
    }
    for variant_data in data["productVariants"]:
        variant_data.pop("id")
        assert variant_data["sku"] in expected_result
        expected_variant = expected_result[variant_data["sku"]]
        expected_channel_listing = expected_variant["channelListings"]
        assert all(
            [
                channelListing in expected_channel_listing
                for channelListing in variant_data["channelListings"]
            ]
        )


def test_product_variant_bulk_create_preorder_channel_listings_input(
    staff_api_client,
    product_available_in_many_channels,
    permission_manage_products,
    size_attribute,
    channel_USD,
    channel_PLN,
):
    product = product_available_in_many_channels
    ProductChannelListing.objects.filter(product=product, channel=channel_PLN).update(
        is_published=False
    )
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_value_count = size_attribute.values.count()
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    attribute_value = size_attribute.values.last()

    global_threshold = 10
    end_date = (
        (datetime.now() + timedelta(days=3))
        .astimezone()
        .replace(microsecond=0)
        .isoformat()
    )

    variants = [
        {
            "sku": str(uuid4())[:12],
            "channelListings": [
                {
                    "price": 10.0,
                    "costPrice": 11.0,
                    "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                    "preorderThreshold": 5,
                }
            ],
            "attributes": [{"id": size_attribute_id, "values": [attribute_value.name]}],
            "preorder": {
                "globalThreshold": global_threshold,
                "endDate": end_date,
            },
        },
        {
            "sku": str(uuid4())[:12],
            "attributes": [{"id": size_attribute_id, "values": ["Test-attribute"]}],
            "channelListings": [
                {
                    "price": 15.0,
                    "costPrice": 16.0,
                    "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                    "preorderThreshold": None,
                },
                {
                    "price": 12.0,
                    "costPrice": 13.0,
                    "channelId": graphene.Node.to_global_id("Channel", channel_PLN.pk),
                    "preorderThreshold": 4,
                },
            ],
            "preorder": {
                "globalThreshold": global_threshold,
                "endDate": end_date,
            },
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert not data["errors"]
    assert data["count"] == 2
    assert product_variant_count + 2 == ProductVariant.objects.count()
    assert attribute_value_count + 1 == size_attribute.values.count()

    expected_result = {
        variants[0]["sku"]: {
            "sku": variants[0]["sku"],
            "channelListings": [{"preorderThreshold": {"quantity": 5}}],
            "preorder": {
                "globalThreshold": global_threshold,
                "endDate": end_date,
            },
        },
        variants[1]["sku"]: {
            "sku": variants[1]["sku"],
            "channelListings": [
                {"preorderThreshold": {"quantity": None}},
                {"preorderThreshold": {"quantity": 4}},
            ],
            "preorder": {
                "globalThreshold": global_threshold,
                "endDate": end_date,
            },
        },
    }
    for variant_data in data["productVariants"]:
        variant_data.pop("id")
        assert variant_data["sku"] in expected_result
        expected_variant = expected_result[variant_data["sku"]]
        expected_channel_listing_thresholds = [
            channel_listing["preorderThreshold"]["quantity"]
            for channel_listing in expected_variant["channelListings"]
        ]
        assert all(
            [
                channel_listing["preorderThreshold"]["quantity"]
                in expected_channel_listing_thresholds
                for channel_listing in variant_data["channelListings"]
            ]
        )
        preorder_data = variant_data["preorder"]
        assert preorder_data["globalThreshold"] == global_threshold
        assert preorder_data["endDate"] == end_date


def test_product_variant_bulk_create_duplicated_channels(
    staff_api_client,
    product_available_in_many_channels,
    permission_manage_products,
    warehouses,
    size_attribute,
    channel_USD,
):
    product = product_available_in_many_channels
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    attribute_value = size_attribute.values.last()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    variants = [
        {
            "sku": str(uuid4())[:12],
            "channelListings": [
                {"price": 10.0, "channelId": channel_id},
                {"price": 10.0, "channelId": channel_id},
            ],
            "attributes": [{"id": size_attribute_id, "values": [attribute_value.name]}],
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "channelListings"
    assert error["code"] == ProductErrorCode.DUPLICATED_INPUT_ITEM.name
    assert error["index"] == 0
    assert error["channels"] == [channel_id]
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_too_many_decimal_places_in_price(
    staff_api_client,
    product_available_in_many_channels,
    permission_manage_products,
    size_attribute,
    channel_USD,
    channel_PLN,
):
    product = product_available_in_many_channels
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    attribute_value = size_attribute.values.last()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.pk)
    variants = [
        {
            "sku": str(uuid4())[:12],
            "channelListings": [
                {"price": 10.1234, "costPrice": 10.1234, "channelId": channel_id},
                {"price": 10.12345, "costPrice": 10.12345, "channelId": channel_pln_id},
            ],
            "attributes": [{"id": size_attribute_id, "values": [attribute_value.name]}],
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert len(data["errors"]) == 4
    errors = data["errors"]
    assert errors[0]["field"] == "price"
    assert errors[0]["code"] == ProductErrorCode.INVALID.name
    assert errors[0]["index"] == 0
    assert errors[0]["channels"] == [channel_id]
    assert errors[1]["field"] == "price"
    assert errors[1]["code"] == ProductErrorCode.INVALID.name
    assert errors[1]["index"] == 0
    assert errors[1]["channels"] == [channel_pln_id]
    assert errors[2]["field"] == "costPrice"
    assert errors[2]["code"] == ProductErrorCode.INVALID.name
    assert errors[2]["index"] == 0
    assert errors[2]["channels"] == [channel_id]
    assert errors[3]["field"] == "costPrice"
    assert errors[3]["code"] == ProductErrorCode.INVALID.name
    assert errors[3]["index"] == 0
    assert errors[3]["channels"] == [channel_pln_id]
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_product_not_assigned_to_channel(
    staff_api_client,
    product,
    permission_manage_products,
    warehouses,
    size_attribute,
    channel_PLN,
):
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    assert not ProductChannelListing.objects.filter(
        product=product, channel=channel_PLN
    ).exists()
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    attribute_value = size_attribute.values.last()
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.pk)
    variants = [
        {
            "sku": str(uuid4())[:12],
            "channelListings": [{"price": 10.0, "channelId": channel_id}],
            "attributes": [{"id": size_attribute_id, "values": [attribute_value.name]}],
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "channelId"
    assert error["code"] == ProductErrorCode.PRODUCT_NOT_ASSIGNED_TO_CHANNEL.name
    assert error["index"] == 0
    assert error["channels"] == [channel_id]
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_duplicated_sku(
    staff_api_client,
    product,
    product_with_default_variant,
    size_attribute,
    permission_manage_products,
):
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    sku = product.variants.first().sku
    sku2 = product_with_default_variant.variants.first().sku
    assert not sku == sku2
    variants = [
        {
            "sku": sku,
            "attributes": [{"id": size_attribute_id, "values": ["Test-value"]}],
        },
        {
            "sku": sku2,
            "attributes": [{"id": size_attribute_id, "values": ["Test-valuee"]}],
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert len(data["errors"]) == 2
    errors = data["errors"]
    for index, error in enumerate(errors):
        assert error["field"] == "sku"
        assert error["code"] == ProductErrorCode.UNIQUE.name
        assert error["index"] == index
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_duplicated_sku_in_input(
    staff_api_client, product, size_attribute, permission_manage_products
):
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "attributes": [{"id": size_attribute_id, "values": ["Test-value"]}],
        },
        {
            "sku": sku,
            "attributes": [{"id": size_attribute_id, "values": ["Test-value2"]}],
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "sku"
    assert error["code"] == ProductErrorCode.UNIQUE.name
    assert error["index"] == 1
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_without_sku(
    staff_api_client, product, size_attribute, permission_manage_products
):
    product_variant_count = ProductVariant.objects.count()
    attribute_value_count = size_attribute.values.count()
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_value = size_attribute.values.last()
    variants = [
        {
            "sku": " ",
            "attributes": [{"id": size_attribute_id, "values": [attribute_value.name]}],
        },
        {
            "sku": None,
            "attributes": [{"id": size_attribute_id, "values": ["Test-attribute"]}],
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert not data["errors"]
    assert data["count"] == 2
    assert product_variant_count + 2 == ProductVariant.objects.count()
    assert attribute_value_count + 1 == size_attribute.values.count()
    assert ProductVariant.objects.filter(sku__isnull=True).count() == 2


def test_product_variant_bulk_create_many_errors(
    staff_api_client, product, size_attribute, permission_manage_products
):
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    non_existent_attribute_pk = 0
    invalid_attribute_id = graphene.Node.to_global_id(
        "Attribute", non_existent_attribute_pk
    )
    sku = product.variants.first().sku
    variants = [
        {
            "sku": str(uuid4())[:12],
            "attributes": [{"id": size_attribute_id, "values": ["Test-value1"]}],
        },
        {
            "sku": str(uuid4())[:12],
            "attributes": [{"id": size_attribute_id, "values": ["Test-value4"]}],
        },
        {
            "sku": sku,
            "attributes": [{"id": size_attribute_id, "values": ["Test-value2"]}],
        },
        {
            "sku": str(uuid4())[:12],
            "attributes": [{"id": invalid_attribute_id, "values": ["Test-value3"]}],
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert len(data["errors"]) == 2
    errors = data["errors"]
    expected_errors = [
        {
            "field": "sku",
            "index": 2,
            "code": ProductErrorCode.UNIQUE.name,
            "message": ANY,
            "warehouses": None,
            "channels": None,
        },
        {
            "field": "attributes",
            "index": 3,
            "code": ProductErrorCode.NOT_FOUND.name,
            "message": ANY,
            "warehouses": None,
            "channels": None,
        },
    ]
    for expected_error in expected_errors:
        assert expected_error in errors
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_two_variants_duplicated_attribute_value(
    staff_api_client,
    product_with_variant_with_two_attributes,
    color_attribute,
    size_attribute,
    permission_manage_products,
):
    product = product_with_variant_with_two_attributes
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.id)
    variants = [
        {
            "sku": str(uuid4())[:12],
            "attributes": [
                {"id": color_attribute_id, "values": ["red"]},
                {"id": size_attribute_id, "values": ["small"]},
            ],
        }
    ]
    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "attributes"
    assert error["code"] == ProductErrorCode.DUPLICATED_INPUT_ITEM.name
    assert error["index"] == 0
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_two_variants_duplicated_attribute_value_in_input(
    staff_api_client,
    product_with_variant_with_two_attributes,
    permission_manage_products,
    color_attribute,
    size_attribute,
):
    product = product_with_variant_with_two_attributes
    product_id = graphene.Node.to_global_id("Product", product.pk)
    product_variant_count = ProductVariant.objects.count()
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.id)
    attributes = [
        {"id": color_attribute_id, "values": [color_attribute.values.last().slug]},
        {"id": size_attribute_id, "values": [size_attribute.values.last().slug]},
    ]
    variants = [
        {"sku": str(uuid4())[:12], "attributes": attributes},
        {"sku": str(uuid4())[:12], "attributes": attributes},
    ]
    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "attributes"
    assert error["code"] == ProductErrorCode.DUPLICATED_INPUT_ITEM.name
    assert error["index"] == 1
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_two_variants_duplicated_one_attribute_value(
    staff_api_client,
    product_with_variant_with_two_attributes,
    color_attribute,
    size_attribute,
    permission_manage_products,
):
    product = product_with_variant_with_two_attributes
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.id)
    variants = [
        {
            "sku": str(uuid4())[:12],
            "attributes": [
                {"id": color_attribute_id, "values": ["red"]},
                {"id": size_attribute_id, "values": ["big"]},
            ],
        }
    ]
    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert not data["errors"]
    assert data["count"] == 1
    assert product_variant_count + 1 == ProductVariant.objects.count()


VARIANT_STOCKS_CREATE_MUTATION = """
    mutation ProductVariantStocksCreate($variantId: ID!, $stocks: [StockInput!]!){
        productVariantStocksCreate(variantId: $variantId, stocks: $stocks){
            productVariant{
                id
                stocks {
                    quantity
                    quantityAllocated
                    id
                    warehouse{
                        slug
                    }
                }
            }
            errors{
                code
                field
                message
                index
            }
        }
    }
"""


def test_variant_stocks_create(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "quantity": 20,
        },
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", second_warehouse.id),
            "quantity": 100,
        },
    ]
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]

    expected_result = [
        {
            "quantity": stocks[0]["quantity"],
            "quantityAllocated": 0,
            "warehouse": {"slug": warehouse.slug},
        },
        {
            "quantity": stocks[1]["quantity"],
            "quantityAllocated": 0,
            "warehouse": {"slug": second_warehouse.slug},
        },
    ]
    assert not data["errors"]
    assert len(data["productVariant"]["stocks"]) == len(stocks)
    result = []
    for stock in data["productVariant"]["stocks"]:
        stock.pop("id")
        result.append(stock)
    for res in result:
        assert res in expected_result


def test_variant_stocks_create_empty_stock_input(
    staff_api_client, variant, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {"variantId": variant_id, "stocks": []}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]

    assert not data["errors"]
    assert len(data["productVariant"]["stocks"]) == variant.stocks.count()
    assert data["productVariant"]["id"] == variant_id


def test_variant_stocks_create_stock_already_exists(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=10)

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "quantity": 20,
        },
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", second_warehouse.id),
            "quantity": 100,
        },
    ]
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]
    errors = data["errors"]

    assert errors
    assert errors[0]["code"] == StockErrorCode.UNIQUE.name
    assert errors[0]["field"] == "warehouse"
    assert errors[0]["index"] == 0


def test_variant_stocks_create_stock_duplicated_warehouse(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    second_warehouse_id = graphene.Node.to_global_id("Warehouse", second_warehouse.id)

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "quantity": 20,
        },
        {"warehouse": second_warehouse_id, "quantity": 100},
        {"warehouse": second_warehouse_id, "quantity": 120},
    ]
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]
    errors = data["errors"]

    assert errors
    assert errors[0]["code"] == StockErrorCode.UNIQUE.name
    assert errors[0]["field"] == "warehouse"
    assert errors[0]["index"] == 2


def test_variant_stocks_create_stock_duplicated_warehouse_and_warehouse_already_exists(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    second_warehouse_id = graphene.Node.to_global_id("Warehouse", second_warehouse.id)
    Stock.objects.create(
        product_variant=variant, warehouse=second_warehouse, quantity=10
    )

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "quantity": 20,
        },
        {"warehouse": second_warehouse_id, "quantity": 100},
        {"warehouse": second_warehouse_id, "quantity": 120},
    ]

    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]
    errors = data["errors"]

    assert len(errors) == 3
    assert {error["code"] for error in errors} == {
        StockErrorCode.UNIQUE.name,
    }
    assert {error["field"] for error in errors} == {
        "warehouse",
    }
    assert {error["index"] for error in errors} == {1, 2}


VARIANT_STOCKS_UPDATE_MUTATIONS = """
    mutation ProductVariantStocksUpdate($variantId: ID!, $stocks: [StockInput!]!){
        productVariantStocksUpdate(variantId: $variantId, stocks: $stocks){
            productVariant{
                stocks{
                    quantity
                    quantityAllocated
                    id
                    warehouse{
                        slug
                    }
                }
            }
            errors{
                code
                field
                message
                index
            }
        }
    }
"""


def test_product_variant_stocks_update(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=10)

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "quantity": 20,
        },
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", second_warehouse.id),
            "quantity": 100,
        },
    ]
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_UPDATE_MUTATIONS,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksUpdate"]

    expected_result = [
        {
            "quantity": stocks[0]["quantity"],
            "quantityAllocated": 0,
            "warehouse": {"slug": warehouse.slug},
        },
        {
            "quantity": stocks[1]["quantity"],
            "quantityAllocated": 0,
            "warehouse": {"slug": second_warehouse.slug},
        },
    ]
    assert not data["errors"]
    assert len(data["productVariant"]["stocks"]) == len(stocks)
    result = []
    for stock in data["productVariant"]["stocks"]:
        stock.pop("id")
        result.append(stock)
    for res in result:
        assert res in expected_result


def test_product_variant_stocks_update_with_empty_stock_list(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    stocks = []
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_UPDATE_MUTATIONS,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksUpdate"]

    assert not data["errors"]
    assert len(data["productVariant"]["stocks"]) == len(stocks)


def test_variant_stocks_update_stock_duplicated_warehouse(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=10)

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        },
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", second_warehouse.pk),
            "quantity": 100,
        },
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 150,
        },
    ]
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_UPDATE_MUTATIONS,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksUpdate"]
    errors = data["errors"]

    assert errors
    assert errors[0]["code"] == StockErrorCode.UNIQUE.name
    assert errors[0]["field"] == "warehouse"
    assert errors[0]["index"] == 2


def test_product_variant_stocks_update_too_big_quantity_value(
    staff_api_client, variant, warehouse, permission_manage_products
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=10)

    quantity = 99999999999
    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", second_warehouse.id),
            "quantity": 99999999999,
        },
    ]
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(VARIANT_STOCKS_UPDATE_MUTATIONS, variables)
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1
    assert (
        content["errors"][0]["message"]
        == f"Int cannot represent non 32-bit signed integer value: {quantity}"
    )


VARIANT_STOCKS_DELETE_MUTATION = """
    mutation ProductVariantStocksDelete($variantId: ID!, $warehouseIds: [ID!]!){
        productVariantStocksDelete(
            variantId: $variantId, warehouseIds: $warehouseIds
        ){
            productVariant{
                stocks{
                    id
                    quantity
                    warehouse{
                        slug
                    }
                }
            }
            errors{
                field
                code
                message
            }
        }
    }
"""


def test_product_variant_stocks_delete_mutation(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=10),
            Stock(product_variant=variant, warehouse=second_warehouse, quantity=140),
        ]
    )
    stocks_count = variant.stocks.count()

    warehouse_ids = [graphene.Node.to_global_id("Warehouse", second_warehouse.id)]

    variables = {"variantId": variant_id, "warehouseIds": warehouse_ids}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksDelete"]

    variant.refresh_from_db()
    assert not data["errors"]
    assert (
        len(data["productVariant"]["stocks"])
        == variant.stocks.count()
        == stocks_count - 1
    )
    assert data["productVariant"]["stocks"][0]["quantity"] == 10
    assert data["productVariant"]["stocks"][0]["warehouse"]["slug"] == warehouse.slug


def test_product_variant_stocks_delete_mutation_invalid_warehouse_id(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.bulk_create(
        [Stock(product_variant=variant, warehouse=warehouse, quantity=10)]
    )
    stocks_count = variant.stocks.count()

    warehouse_ids = [graphene.Node.to_global_id("Warehouse", second_warehouse.id)]

    variables = {"variantId": variant_id, "warehouseIds": warehouse_ids}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksDelete"]

    variant.refresh_from_db()
    assert not data["errors"]
    assert (
        len(data["productVariant"]["stocks"]) == variant.stocks.count() == stocks_count
    )
    assert data["productVariant"]["stocks"][0]["quantity"] == 10
    assert data["productVariant"]["stocks"][0]["warehouse"]["slug"] == warehouse.slug


def test_product_variant_stocks_delete_mutation_invalid_object_type_of_warehouse_id(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    Stock.objects.bulk_create(
        [Stock(product_variant=variant, warehouse=warehouse, quantity=10)]
    )

    warehouse_ids = [graphene.Node.to_global_id("Product", warehouse.id)]

    variables = {"variantId": variant_id, "warehouseIds": warehouse_ids}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksDelete"]

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.GRAPHQL_ERROR.name
    assert errors[0]["field"] == "warehouseIds"


VARIANT_UPDATE_AND_STOCKS_REMOVE_MUTATION = """
  fragment ProductVariant on ProductVariant {
    stocks {
      id
    }
  }

  mutation VariantUpdate($removeStocks: [ID!]!, $id: ID!) {
    productVariantUpdate(id: $id, input: {}) {
      productVariant {
        ...ProductVariant
      }
    }
    productVariantStocksDelete(variantId: $id, warehouseIds: $removeStocks) {
      productVariant {
        ...ProductVariant
      }
    }
  }
"""


def test_invalidate_stocks_dataloader_on_removing_stocks(
    staff_api_client, variant_with_many_stocks, permission_manage_products
):
    # given
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", stock.warehouse.id)
        for stock in variant_with_many_stocks.stocks.all()
    ]
    variables = {
        "id": variant_id,
        "removeStocks": warehouse_ids,
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_UPDATE_AND_STOCKS_REMOVE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    variant_data = content["data"]["productVariantUpdate"]["productVariant"]
    remove_stocks_data = content["data"]["productVariantStocksDelete"]["productVariant"]

    # no stocks were removed in the first mutation
    assert len(variant_data["stocks"]) == len(warehouse_ids)

    # stocks are empty in the second mutation
    assert remove_stocks_data["stocks"] == []


VARIANT_UPDATE_AND_STOCKS_CREATE_MUTATION = """
  fragment ProductVariant on ProductVariant {
    id
    name
    stocks {
      quantity
      warehouse {
        id
        name
      }
    }
  }

  mutation VariantUpdate($id: ID!, $stocks: [StockInput!]!) {
    productVariantUpdate(id: $id, input: {}) {
      productVariant {
        ...ProductVariant
      }
    }
    productVariantStocksCreate(variantId: $id, stocks: $stocks) {
      productVariant {
        ...ProductVariant
      }
    }
  }
"""


def test_invalidate_stocks_dataloader_on_create_stocks(
    staff_api_client, variant_with_many_stocks, permission_manage_products
):
    # given
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", stock.warehouse.id)
        for stock in variant_with_many_stocks.stocks.all()
    ]
    variant.stocks.all().delete()
    variables = {
        "id": variant_id,
        "stocks": [
            {"warehouse": warehouse_id, "quantity": 10}
            for warehouse_id in warehouse_ids
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_UPDATE_AND_STOCKS_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    variant_data = content["data"]["productVariantUpdate"]["productVariant"]
    create_stocks_data = content["data"]["productVariantStocksCreate"]["productVariant"]

    # no stocks are present after the first mutation
    assert variant_data["stocks"] == []

    # stocks are returned in the second mutation, after dataloader invalidation
    assert len(create_stocks_data["stocks"]) == len(warehouse_ids)


VARIANT_UPDATE_AND_STOCKS_UPDATE_MUTATION = """
  fragment ProductVariant on ProductVariant {
    id
    name
    stocks {
      quantity
      warehouse {
        id
        name
      }
    }
  }

  mutation VariantUpdate($id: ID!, $stocks: [StockInput!]!) {
    productVariantUpdate(id: $id, input: {}) {
      productVariant {
        ...ProductVariant
      }
    }
    productVariantStocksUpdate(variantId: $id, stocks: $stocks) {
      productVariant {
        ...ProductVariant
      }
    }
  }
"""


def test_invalidate_stocks_dataloader_on_update_stocks(
    staff_api_client, variant_with_many_stocks, permission_manage_products
):
    # given
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    stock = variant.stocks.first()
    # keep only one stock record for test purposes
    variant.stocks.exclude(id=stock.id).delete()
    warehouse_id = graphene.Node.to_global_id("Warehouse", stock.warehouse.id)
    old_quantity = stock.quantity
    new_quantity = old_quantity + 500
    variables = {
        "id": variant_id,
        "stocks": [{"warehouse": warehouse_id, "quantity": new_quantity}],
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_UPDATE_AND_STOCKS_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    variant_data = content["data"]["productVariantUpdate"]["productVariant"]
    update_stocks_data = content["data"]["productVariantStocksUpdate"]["productVariant"]

    # stocks is not updated in the first mutation
    assert variant_data["stocks"][0]["quantity"] == old_quantity

    # stock is updated in the second mutation
    assert update_stocks_data["stocks"][0]["quantity"] == new_quantity


def test_query_product_variant_for_federation(api_client, variant, channel_USD):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "representations": [
            {
                "__typename": "ProductVariant",
                "id": variant_id,
                "channel": channel_USD.slug,
            },
        ],
    }
    query = """
      query GetProductVariantInFederation($representations: [_Any]) {
        _entities(representations: $representations) {
          __typename
          ... on ProductVariant {
            id
            name
          }
        }
      }
    """

    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "ProductVariant",
            "id": variant_id,
            "name": variant.name,
        }
    ]


QUERY_VARIANT_DEACTIVATE_PREORDER = """
    mutation deactivatePreorder (
        $id: ID!
        ) {
            productVariantPreorderDeactivate(id: $id) {
                productVariant {
                    sku
                    preorder {
                        globalThreshold
                        endDate
                    }
                    stocks {
                        quantityAllocated
                    }
                }
                errors {
                    field
                    code
                    message
                }
            }
        }
"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_product_variant_deactivate_preorder(
    updated_webhook_mock,
    staff_api_client,
    permission_manage_products,
    preorder_variant_global_and_channel_threshold,
    preorder_allocation,
):
    variant = preorder_variant_global_and_channel_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    allocations_before = Allocation.objects.filter(
        stock__product_variant_id=variant.pk
    ).count()

    response = staff_api_client.post_graphql(
        QUERY_VARIANT_DEACTIVATE_PREORDER,
        {"id": variant_id},
        permissions=[permission_manage_products],
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantPreorderDeactivate"]["productVariant"]

    assert not data["preorder"]
    assert data["stocks"][0]["quantityAllocated"] > allocations_before

    updated_webhook_mock.assert_called_once_with(variant)


def test_product_variant_deactivate_preorder_non_preorder_variant(
    staff_api_client,
    permission_manage_products,
    variant,
):
    assert variant.is_preorder is False
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    response = staff_api_client.post_graphql(
        QUERY_VARIANT_DEACTIVATE_PREORDER,
        {"id": variant_id},
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    error = content["data"]["productVariantPreorderDeactivate"]["errors"][0]

    assert error["field"] == "id"
    assert error["code"] == ProductErrorCode.INVALID.name


@patch("saleor.graphql.product.mutations.products.deactivate_preorder_for_variant")
def test_product_variant_deactivate_preorder_cannot_deactivate(
    mock_deactivate_preorder_for_variant,
    staff_api_client,
    permission_manage_products,
    preorder_variant_global_and_channel_threshold,
    preorder_allocation,
):
    variant = preorder_variant_global_and_channel_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    mock_deactivate_preorder_for_variant.side_effect = PreorderAllocationError(
        preorder_allocation.order_line
    )

    response = staff_api_client.post_graphql(
        QUERY_VARIANT_DEACTIVATE_PREORDER,
        {"id": variant_id},
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    error = content["data"]["productVariantPreorderDeactivate"]["errors"][0]

    assert error["field"] is None
    assert error["code"] == ProductErrorCode.PREORDER_VARIANT_CANNOT_BE_DEACTIVATED.name


def test_product_variant_deactivate_preorder_as_customer(
    user_api_client,
    preorder_variant_global_and_channel_threshold,
):
    variant = preorder_variant_global_and_channel_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    response = user_api_client.post_graphql(
        QUERY_VARIANT_DEACTIVATE_PREORDER,
        {"id": variant_id},
    )

    assert_no_permission(response)


def test_product_variant_deactivate_preorder_as_anonymous(
    api_client,
    preorder_variant_global_and_channel_threshold,
):
    variant = preorder_variant_global_and_channel_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    response = api_client.post_graphql(
        QUERY_VARIANT_DEACTIVATE_PREORDER,
        {"id": variant_id},
    )

    assert_no_permission(response)


def test_product_variant_deactivate_preorder_as_app_with_permission(
    app_api_client,
    preorder_variant_global_and_channel_threshold,
    permission_manage_products,
):
    variant = preorder_variant_global_and_channel_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    response = app_api_client.post_graphql(
        QUERY_VARIANT_DEACTIVATE_PREORDER,
        {"id": variant_id},
        permissions=[permission_manage_products],
    )

    content = get_graphql_content(response)
    data = content["data"]["productVariantPreorderDeactivate"]["productVariant"]
    assert not data["preorder"]


def test_product_variant_deactivate_preorder_as_app(
    app_api_client,
    preorder_variant_global_and_channel_threshold,
):
    variant = preorder_variant_global_and_channel_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    response = app_api_client.post_graphql(
        QUERY_VARIANT_DEACTIVATE_PREORDER,
        {"id": variant_id},
    )

    assert_no_permission(response)


VARIANT_CREATE_MUTATION = """
    mutation variantCreate($input: ProductVariantCreateInput!) {
        productVariantCreate (input: $input)
        {
            productVariant {
                id
            }
            errors {
                field,
                message,
                code,
                attributes
            }
        }
    }
"""


def test_variant_create_product_without_variant_attributes(
    product_with_product_attributes, staff_api_client, permission_manage_products
):
    product = product_with_product_attributes

    prod_id = graphene.Node.to_global_id("Product", product.pk)
    attr_id = graphene.Node.to_global_id(
        "Attribute", product.product_type.product_attributes.first().pk
    )
    input = {
        "sku": "my-sku",
        "product": prod_id,
        "attributes": [{"id": attr_id, "values": ["1"]}],
    }
    response = staff_api_client.post_graphql(
        VARIANT_CREATE_MUTATION,
        variables={"input": input},
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    errors = content["data"]["productVariantCreate"]["errors"]
    assert errors
    assert errors[0]["code"] == ProductErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED.name
    assert len(errors[0]["attributes"]) == 1
    assert errors[0]["attributes"][0] == attr_id


def test_variant_create_product_with_variant_attributes_variant_flag_false(
    product_with_variant_attributes, staff_api_client, permission_manage_products
):
    product = product_with_variant_attributes

    product_type = product.product_type
    product_type.has_variants = False
    product_type.save()

    prod_id = graphene.Node.to_global_id("Product", product.pk)
    attr_id = graphene.Node.to_global_id(
        "Attribute", product.product_type.variant_attributes.first().pk
    )

    input = {
        "sku": "my-sku",
        "product": prod_id,
        "attributes": [{"id": attr_id, "values": ["1"]}],
    }
    response = staff_api_client.post_graphql(
        VARIANT_CREATE_MUTATION,
        variables={"input": input},
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    errors = content["data"]["productVariantCreate"]["errors"]
    assert errors
    assert errors[0]["code"] == ProductErrorCode.INVALID.name
