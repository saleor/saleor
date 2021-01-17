from unittest.mock import ANY, patch
from uuid import uuid4

import graphene
import pytest
from django.utils.text import slugify
from measurement.measures import Weight
from prices import Money, TaxedMoney

from ....attribute import AttributeInputType
from ....attribute.models import AttributeValue
from ....attribute.utils import associate_attribute_values_to_instance
from ....core.weight import WeightUnits
from ....order import OrderStatus
from ....order.models import OrderLine
from ....product.error_codes import ProductErrorCode
from ....product.models import Product, ProductChannelListing, ProductVariant
from ....warehouse.error_codes import StockErrorCode
from ....warehouse.models import Stock, Warehouse
from ...core.enums import WeightUnitsEnum
from ...tests.utils import assert_no_permission, get_graphql_content


def test_fetch_variant(
    staff_api_client,
    product,
    permission_manage_products,
    site_settings,
    channel_USD,
):
    query = """
    query ProductVariantDetails($id: ID!, $countyCode: CountryCode, $channel: String) {
        productVariant(id: $id, channel: $channel) {
            id
            stocks(countryCode: $countyCode) {
                id
            }
            attributes {
                attribute {
                    id
                    name
                    slug
                    values {
                        id
                        name
                        slug
                    }
                }
                values {
                    id
                    name
                    slug
                }
            }
            costPrice {
                currency
                amount
            }
            images {
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
        }
    }
    """
    # given
    variant = product.variants.first()
    variant.weight = Weight(kg=10)
    variant.save(update_fields=["weight"])

    site_settings.default_weight_unit = WeightUnits.GRAM
    site_settings.save(update_fields=["default_weight_unit"])

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "countyCode": "EU", "channel": channel_USD.slug}
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["name"] == variant.name
    assert len(data["stocks"]) == variant.stocks.count()
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


CREATE_VARIANT_MUTATION = """
      mutation createVariant (
            $productId: ID!,
            $sku: String,
            $stocks: [StockInput!],
            $attributes: [AttributeValueInput]!,
            $weight: WeightScalar,
            $trackInventory: Boolean) {
                productVariantCreate(
                    input: {
                        product: $productId,
                        sku: $sku,
                        stocks: $stocks,
                        attributes: $attributes,
                        trackInventory: $trackInventory,
                        weight: $weight
                    }) {
                    productErrors {
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
                                file {
                                    url
                                    contentType
                                }
                            }
                        }
                        costPrice {
                            currency
                            amount
                            localized
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
                    }
                }
            }

"""


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_create_variant(
    updated_webhook_mock,
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
    variant_id = graphene.Node.to_global_id(
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
        "attributes": [{"id": variant_id, "values": [variant_value]}],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    assert not content["productErrors"]
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
    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_create_variant_with_file_attribute(
    updated_webhook_mock,
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
    assert not content["productErrors"]
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

    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_create_variant_with_file_attribute_new_value(
    updated_webhook_mock,
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
    assert not content["productErrors"]
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

    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_create_variant_with_file_attribute_no_file_url_given(
    updated_webhook_mock,
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
    errors = content["productErrors"]
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

    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_create_variant_with_page_reference_attribute(
    updated_webhook_mock,
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
    assert not content["productErrors"]
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
            "reference": page_ref_1,
            "name": page_list[0].title,
        },
        {
            "slug": f"{variant_pk}_{page_list[1].pk}",
            "file": None,
            "reference": page_ref_2,
            "name": page_list[1].title,
        },
    ]
    for value in expected_values:
        assert value in data["attributes"][0]["values"]
    assert len(data["stocks"]) == 1
    assert data["stocks"][0]["quantity"] == stocks[0]["quantity"]
    assert data["stocks"][0]["warehouse"]["slug"] == warehouse.slug

    product_type_page_reference_attribute.refresh_from_db()
    assert product_type_page_reference_attribute.values.count() == values_count + 2

    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_create_variant_with_page_reference_attribute_no_references_given(
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
    errors = content["productErrors"]
    data = content["productVariant"]
    assert not data
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [ref_attr_id]

    product_type_page_reference_attribute.refresh_from_db()
    assert product_type_page_reference_attribute.values.count() == values_count

    updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_create_variant_with_product_reference_attribute(
    updated_webhook_mock,
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
    assert not content["productErrors"]
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
            "reference": product_ref_1,
            "name": product_list[0].name,
        },
        {
            "slug": f"{variant_pk}_{product_list[1].pk}",
            "file": None,
            "reference": product_ref_2,
            "name": product_list[1].name,
        },
    ]
    for value in expected_values:
        assert value in data["attributes"][0]["values"]
    assert len(data["stocks"]) == 1
    assert data["stocks"][0]["quantity"] == stocks[0]["quantity"]
    assert data["stocks"][0]["warehouse"]["slug"] == warehouse.slug

    product_type_product_reference_attribute.refresh_from_db()
    assert product_type_product_reference_attribute.values.count() == values_count + 2

    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_create_variant_with_product_reference_attribute_no_references_given(
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
    errors = content["productErrors"]
    data = content["productVariant"]
    assert not data
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [ref_attr_id]

    product_type_product_reference_attribute.refresh_from_db()
    assert product_type_product_reference_attribute.values.count() == values_count

    updated_webhook_mock.assert_not_called()


def test_create_product_variant_with_negative_weight(
    staff_api_client, product, product_type, permission_manage_products
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)

    variant_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().pk
    )
    variant_value = "test-value"

    variables = {
        "productId": product_id,
        "weight": -1,
        "attributes": [{"id": variant_id, "values": [variant_value]}],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantCreate"]
    error = data["productErrors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


def test_create_product_variant_without_attributes(
    staff_api_client, product, permission_manage_products
):
    # given
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
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
    error = data["productErrors"][0]

    assert error["field"] == "attributes"
    assert error["code"] == ProductErrorCode.REQUIRED.name


def test_create_product_variant_not_all_attributes(
    staff_api_client, product, product_type, color_attribute, permission_manage_products
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    variant_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().pk
    )
    variant_value = "test-value"
    product_type.variant_attributes.add(color_attribute)

    variables = {
        "productId": product_id,
        "sku": sku,
        "attributes": [{"id": variant_id, "values": [variant_value]}],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["productVariantCreate"]["productErrors"]
    assert content["data"]["productVariantCreate"]["productErrors"][0] == {
        "field": "attributes",
        "code": ProductErrorCode.REQUIRED.name,
        "message": ANY,
        "attributes": None,
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
    assert content["data"]["productVariantCreate"]["productErrors"]
    assert content["data"]["productVariantCreate"]["productErrors"][0] == {
        "field": "attributes",
        "code": ProductErrorCode.DUPLICATED_INPUT_ITEM.name,
        "message": ANY,
        "attributes": None,
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
            {"id": weight_attr_id, "values": [None]},
            {"id": size_attr_id, "values": [non_existent_attr_value, size_value_slug]},
        ],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    data = content["data"]["productVariantCreate"]
    errors = data["productErrors"]

    assert not data["productVariant"]
    assert len(errors) == 2

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
    ]
    for error in expected_errors:
        assert error in errors


def test_create_product_variant_update_with_new_attributes(
    staff_api_client, permission_manage_products, product, size_attribute
):
    query = """
        mutation VariantUpdate(
          $id: ID!
          $attributes: [AttributeValueInput]
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
                  values {
                    id
                    name
                    slug
                    __typename
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

    variables = {
        "attributes": [{"id": size_attribute_id, "values": ["XXXL"]}],
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


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_variant(
    updated_webhook_mock,
    staff_api_client,
    product,
    size_attribute,
    permission_manage_products,
):
    query = """
        mutation updateVariant (
            $id: ID!,
            $sku: String!,
            $trackInventory: Boolean!,
            $attributes: [AttributeValueInput]) {
                productVariantUpdate(
                    id: $id,
                    input: {
                        sku: $sku,
                        trackInventory: $trackInventory,
                        attributes: $attributes,
                    }) {
                    productVariant {
                        name
                        sku
                        channelListings {
                            channel {
                                slug
                            }
                        }
                        costPrice {
                            currency
                            amount
                            localized
                        }
                    }
                }
            }

    """
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    sku = "test sku"

    variables = {
        "id": variant_id,
        "sku": sku,
        "trackInventory": True,
        "attributes": [{"id": attribute_id, "values": ["S"]}],
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]["productVariant"]
    assert data["name"] == variant.name
    assert data["sku"] == sku
    updated_webhook_mock.assert_called_once_with(product)


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
                productErrors {
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
    error = data["productErrors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


QUERY_UPDATE_VARIANT_ATTRIBUTES = """
    mutation updateVariant (
        $id: ID!,
        $sku: String,
        $attributes: [AttributeValueInput]!) {
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
                        }
                    }
                }
                errors {
                    field
                    message
                }
                productErrors {
                    field
                    code
                }
            }
        }
"""


def test_update_product_variant_not_all_attributes(
    staff_api_client, product, product_type, color_attribute, permission_manage_products
):
    """Ensures updating a variant with missing attributes (all attributes must
    be provided) raises an error. We expect the color attribute
    to be flagged as missing."""

    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "test sku"
    attr_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().id
    )
    variant_value = "test-value"
    product_type.variant_attributes.add(color_attribute)

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [{"id": attr_id, "values": [variant_value]}],
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    assert len(content["data"]["productVariantUpdate"]["errors"]) == 1
    assert content["data"]["productVariantUpdate"]["errors"][0] == {
        "field": "attributes",
        "message": "All variant selection attributes must take a value.",
    }
    assert not product.variants.filter(sku=sku).exists()


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
    assert data["productErrors"][0] == {
        "field": "attributes",
        "code": ProductErrorCode.DUPLICATED_INPUT_ITEM.name,
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
    assert data["productErrors"][0] == {
        "field": "attributes",
        "code": ProductErrorCode.DUPLICATED_INPUT_ITEM.name,
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
    assert value_data["file"]["url"] == existing_value.file_url
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
    )
    attr_value_2 = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=product_list[1].name,
        slug=f"{variant.pk}_{product_list[1].pk}",
    )
    attr_value_3 = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=product_list[2].name,
        slug=f"{variant.pk}_{product_list[2].pk}",
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
    assert data["productErrors"] == []

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
    "values, message",
    (
        ([], "Attribute expects a value but none were given"),
        (["one", "two"], "Attribute must take only one value"),
        (["   "], "Attribute values cannot be blank"),
        ([None], "Attribute values cannot be blank"),
    ),
)
def test_update_product_variant_requires_values(
    staff_api_client, variant, product_type, permission_manage_products, values, message
):
    """Ensures updating a variant with invalid values raise an error.

    - No values
    - Blank value
    - None as value
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
    }
    assert not variant.product.variants.filter(sku=sku).exists()


def test_update_product_variant_with_price_does_not_raise_price_validation_error(
    staff_api_client, variant, size_attribute, permission_manage_products
):
    mutation = """
    mutation updateVariant ($id: ID!, $attributes: [AttributeValueInput]) {
        productVariantUpdate(
            id: $id,
            input: {
            attributes: $attributes,
        }) {
            productVariant {
                id
            }
            productErrors {
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
    assert not content["data"]["productVariantUpdate"]["productErrors"]


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


def test_delete_variant(staff_api_client, product, permission_manage_products):
    query = DELETE_VARIANT_MUTATION
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantDelete"]
    assert data["productVariant"]["sku"] == variant.sku
    with pytest.raises(variant._meta.model.DoesNotExist):
        variant.refresh_from_db()


def test_delete_variant_in_draft_order(
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
        is_shipping_required=variant.is_shipping_required(),
        unit_price=unit_price,
        total_price=unit_price * quantity,
        quantity=quantity,
    )
    order_line_not_in_draft_pk = order_line_not_in_draft.pk

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    content = get_graphql_content(response)
    data = content["data"]["productVariantDelete"]
    assert data["productVariant"]["sku"] == variant.sku
    with pytest.raises(order_line._meta.model.DoesNotExist):
        order_line.refresh_from_db()

    assert OrderLine.objects.filter(pk=order_line_not_in_draft_pk).exists()


def test_delete_default_variant(
    staff_api_client, product_with_two_variants, permission_manage_products
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


def test_delete_not_default_variant_left_default_variant_unchanged(
    staff_api_client, product_with_two_variants, permission_manage_products
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


def test_delete_default_all_product_variant_left_product_default_variant_unset(
    staff_api_client, product, permission_manage_products
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


def test_product_variants_by_ids(user_api_client, variant, channel_USD):
    query = """
        query getProduct($ids: [ID!], $channel: String) {
            productVariants(ids: $ids, first: 1, channel: $channel) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert data["edges"][0]["node"]["id"] == variant_id
    assert len(data["edges"]) == 1


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

    assert data["totalCount"] == product_count


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

    assert data["totalCount"] == product_count


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


PRODUCT_VARIANT_BULK_CREATE_MUTATION = """
    mutation ProductVariantBulkCreate(
        $variants: [ProductVariantBulkCreateInput]!, $productId: ID!
    ) {
        productVariantBulkCreate(variants: $variants, product: $productId) {
            bulkProductErrors {
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
                }
            }
            count
        }
    }
"""


def test_product_variant_bulk_create_by_attribute_id(
    staff_api_client, product, size_attribute, permission_manage_products
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
    data = content["data"]["productVariantBulkCreate"]
    assert not data["bulkProductErrors"]
    assert data["count"] == 1
    assert data["productVariants"][0]["name"] == attribute_value.name
    assert product_variant_count + 1 == ProductVariant.objects.count()
    assert attribute_value_count == size_attribute.values.count()
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
    assert not data["bulkProductErrors"]
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
    assert not data["bulkProductErrors"]
    assert data["count"] == 1
    assert product_variant_count + 1 == ProductVariant.objects.count()


def test_product_variant_bulk_create_with_new_attribute_value(
    staff_api_client, product, size_attribute, permission_manage_products
):
    product_variant_count = ProductVariant.objects.count()
    attribute_value_count = size_attribute.values.count()
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_value = size_attribute.values.last()
    variants = [
        {
            "sku": str(uuid4())[:12],
            "attributes": [{"id": size_attribute_id, "values": [attribute_value.name]}],
        },
        {
            "sku": str(uuid4())[:12],
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
    assert not data["bulkProductErrors"]
    assert data["count"] == 2
    assert product_variant_count + 2 == ProductVariant.objects.count()
    assert attribute_value_count + 1 == size_attribute.values.count()


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
    assert not data["bulkProductErrors"]
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
    assert not data["bulkProductErrors"]
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
    errors = data["bulkProductErrors"]

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
    assert not data["bulkProductErrors"]
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
    assert len(data["bulkProductErrors"]) == 1
    error = data["bulkProductErrors"][0]
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
    assert len(data["bulkProductErrors"]) == 4
    errors = data["bulkProductErrors"]
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
    assert len(data["bulkProductErrors"]) == 1
    error = data["bulkProductErrors"][0]
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
    assert len(data["bulkProductErrors"]) == 2
    errors = data["bulkProductErrors"]
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
    assert len(data["bulkProductErrors"]) == 1
    error = data["bulkProductErrors"][0]
    assert error["field"] == "sku"
    assert error["code"] == ProductErrorCode.UNIQUE.name
    assert error["index"] == 1
    assert product_variant_count == ProductVariant.objects.count()


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
    assert len(data["bulkProductErrors"]) == 2
    errors = data["bulkProductErrors"]
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
    assert len(data["bulkProductErrors"]) == 1
    error = data["bulkProductErrors"][0]
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
    assert len(data["bulkProductErrors"]) == 1
    error = data["bulkProductErrors"][0]
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
    assert not data["bulkProductErrors"]
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
            bulkStockErrors{
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
    assert not data["bulkStockErrors"]
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

    assert not data["bulkStockErrors"]
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
    errors = data["bulkStockErrors"]

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
    errors = data["bulkStockErrors"]

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
    errors = data["bulkStockErrors"]

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
            bulkStockErrors{
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
    assert not data["bulkStockErrors"]
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

    assert not data["bulkStockErrors"]
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
    errors = data["bulkStockErrors"]

    assert errors
    assert errors[0]["code"] == StockErrorCode.UNIQUE.name
    assert errors[0]["field"] == "warehouse"
    assert errors[0]["index"] == 2


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
            stockErrors{
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
    assert not data["stockErrors"]
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
    assert not data["stockErrors"]
    assert (
        len(data["productVariant"]["stocks"]) == variant.stocks.count() == stocks_count
    )
    assert data["productVariant"]["stocks"][0]["quantity"] == 10
    assert data["productVariant"]["stocks"][0]["warehouse"]["slug"] == warehouse.slug
