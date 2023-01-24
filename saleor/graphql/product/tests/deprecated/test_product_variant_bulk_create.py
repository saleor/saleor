from datetime import datetime, timedelta
from unittest.mock import ANY, patch
from uuid import uuid4

import graphene

from .....attribute import AttributeInputType
from .....product.error_codes import ProductVariantBulkErrorCode
from .....product.models import ProductChannelListing, ProductVariant
from .....tests.utils import flush_post_commit_hooks
from ....tests.utils import get_graphql_content

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
def test_product_variant_bulk_create_by_name(
    product_variant_created_webhook_mock,
    staff_api_client,
    product,
    size_attribute,
    permission_manage_products,
):
    # given
    product_variant_count = ProductVariant.objects.count()
    attribute_value_count = size_attribute.values.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribut_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    attribute_value = size_attribute.values.last()
    sku = str(uuid4())[:12]
    name = "new-variant-anem"
    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
            "name": name,
            "attributes": [{"id": attribut_id, "values": [attribute_value.name]}],
        }
    ]

    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert not data["errors"]
    assert data["count"] == 1
    assert data["productVariants"][0]["name"] == name
    assert product_variant_count + 1 == ProductVariant.objects.count()
    assert attribute_value_count == size_attribute.values.count()
    product_variant = ProductVariant.objects.get(sku=sku)
    product.refresh_from_db()
    assert product.default_variant == product_variant
    assert product_variant_created_webhook_mock.call_count == data["count"]


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
    staff_api_client,
    product_with_single_variant,
    size_attribute,
    permission_manage_products,
):
    product = product_with_single_variant
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
    assert error["code"] == ProductVariantBulkErrorCode.DUPLICATED_INPUT_ITEM.name
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
    assert error["code"] == ProductVariantBulkErrorCode.DUPLICATED_INPUT_ITEM.name
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
    assert errors[0]["code"] == ProductVariantBulkErrorCode.INVALID_PRICE.name
    assert errors[0]["index"] == 0
    assert errors[0]["channels"] == [channel_id]
    assert errors[1]["field"] == "price"
    assert errors[1]["code"] == ProductVariantBulkErrorCode.INVALID_PRICE.name
    assert errors[1]["index"] == 0
    assert errors[1]["channels"] == [channel_pln_id]
    assert errors[2]["field"] == "costPrice"
    assert errors[2]["code"] == ProductVariantBulkErrorCode.INVALID_PRICE.name
    assert errors[2]["index"] == 0
    assert errors[2]["channels"] == [channel_id]
    assert errors[3]["field"] == "costPrice"
    assert errors[3]["code"] == ProductVariantBulkErrorCode.INVALID_PRICE.name
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
    code = ProductVariantBulkErrorCode.PRODUCT_NOT_ASSIGNED_TO_CHANNEL.name
    assert error["field"] == "channelId"
    assert error["code"] == code
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
        assert error["code"] == ProductVariantBulkErrorCode.UNIQUE.name
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
    assert len(data["errors"]) == 2
    error = data["errors"][0]
    assert error["field"] == "sku"
    assert error["code"] == ProductVariantBulkErrorCode.UNIQUE.name
    assert error["index"] == 0
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
    assert len(data["errors"]) == 3
    errors = data["errors"]
    expected_errors = [
        {
            "field": "sku",
            "index": 2,
            "code": ProductVariantBulkErrorCode.UNIQUE.name,
            "message": ANY,
            "warehouses": None,
            "channels": None,
        },
        {
            "field": "attributes",
            "index": 3,
            "code": ProductVariantBulkErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED.name,
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
    assert error["code"] == ProductVariantBulkErrorCode.DUPLICATED_INPUT_ITEM.name
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
    assert error["code"] == ProductVariantBulkErrorCode.DUPLICATED_INPUT_ITEM.name
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
