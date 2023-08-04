import json
from datetime import datetime, timedelta
from unittest.mock import ANY, patch
from uuid import uuid4

import graphene
import pytz
from django.conf import settings
from freezegun import freeze_time

from .....attribute import AttributeInputType
from .....product.error_codes import ProductVariantBulkErrorCode
from .....product.models import (
    ProductChannelListing,
    ProductVariant,
    ProductVariantChannelListing,
)
from .....tests.utils import dummy_editorjs, flush_post_commit_hooks
from ....core.enums import ErrorPolicyEnum
from ....tests.utils import get_graphql_content

PRODUCT_VARIANT_BULK_CREATE_MUTATION = """
    mutation ProductVariantBulkCreate(
        $variants: [ProductVariantBulkCreateInput!]!,
        $productId: ID!,
        $errorPolicy: ErrorPolicyEnum
    ) {
        productVariantBulkCreate(
            variants: $variants, product: $productId, errorPolicy: $errorPolicy
            ) {
                results{
                    productVariant{
                        metadata {
                            key
                            value
                        }
                        id
                        name
                        sku
                        trackInventory
                        attributes{
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
                    errors {
                        field
                        path
                        message
                        code
                        warehouses
                        channels
                    }
                }
            count
        }
    }
"""


@patch("saleor.product.tasks.update_product_discounted_price_task.delay")
@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
def test_product_variant_bulk_create_by_name(
    product_variant_created_webhook_mock,
    update_product_discounted_price_task_mock,
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
    sku1 = str(uuid4())[:12]
    sku2 = str(uuid4())[:12]
    name1 = "new-variant-name"
    name2 = "new-variant-name"
    metadata_key = "md key"
    metadata_value = "md value"

    variants = [
        {
            "sku": sku1,
            "weight": 2.5,
            "trackInventory": True,
            "name": name1,
            "attributes": [{"id": attribut_id, "values": [attribute_value.name]}],
            "metadata": [{"key": metadata_key, "value": metadata_value}],
        },
        {
            "sku": sku2,
            "name": name2,
            "attributes": [{"id": attribut_id, "values": [attribute_value.name]}],
        },
    ]

    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response, ignore_errors=True)
    flush_post_commit_hooks()
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    variant_data = data["results"][0]["productVariant"]
    assert variant_data["name"] == name1
    assert variant_data["metadata"][0]["key"] == metadata_key
    assert variant_data["metadata"][0]["value"] == metadata_value
    assert product_variant_count + 2 == ProductVariant.objects.count()
    assert attribute_value_count == size_attribute.values.count()
    product_variant = ProductVariant.objects.get(sku=sku1)
    product.refresh_from_db()
    assert product.default_variant == product_variant
    assert product_variant_created_webhook_mock.call_count == data["count"]
    update_product_discounted_price_task_mock.call_count == data["count"]


@patch("saleor.product.tasks.update_product_discounted_price_task.delay")
@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
def test_product_variant_bulk_create_by_attribute_id(
    product_variant_created_webhook_mock,
    update_product_discounted_price_task_mock,
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
    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
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
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    assert data["results"][0]["productVariant"]["name"] == attribute_value.name
    assert product_variant_count + 1 == ProductVariant.objects.count()
    assert attribute_value_count == size_attribute.values.count()
    product_variant = ProductVariant.objects.get(sku=sku)
    product.refresh_from_db()
    assert product.default_variant == product_variant
    assert product_variant_created_webhook_mock.call_count == data["count"]
    update_product_discounted_price_task_mock.assert_called_once_with(product.id)


def test_product_variant_bulk_create_by_attribute_external_ref(
    staff_api_client,
    product,
    color_attribute,
    permission_manage_products,
):
    # given
    product_variant_count = ProductVariant.objects.count()
    product.product_type.variant_attributes.add(color_attribute)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_value = color_attribute.values.last()
    attribute_external_ref = color_attribute.external_reference
    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [
                {
                    "externalReference": attribute_external_ref,
                    "dropdown": {
                        "externalReference": attribute_value.external_reference
                    },
                }
            ],
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
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    assert product_variant_count + 1 == ProductVariant.objects.count()
    assert (
        data["results"][0]["productVariant"]["attributes"][1]["attribute"]["slug"]
        == color_attribute.slug
    )
    assert (
        data["results"][0]["productVariant"]["attributes"][1]["values"][0]["slug"]
        == attribute_value.slug
    )


def test_product_variant_bulk_create_return_error_when_attribute_external_ref_and_id(
    staff_api_client,
    product,
    color_attribute,
    permission_manage_products,
):
    # given
    product.product_type.variant_attributes.add(color_attribute)
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_value = color_attribute.values.last()
    attribute_external_ref = color_attribute.external_reference
    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [
                {
                    "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
                    "externalReference": attribute_external_ref,
                    "dropdown": {
                        "externalReference": attribute_value.external_reference
                    },
                }
            ],
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
    assert data["results"][0]["errors"]
    error = data["results"][0]["errors"][0]
    assert error["path"] == "attributes"
    assert error["message"] == (
        "Argument 'id' cannot be combined with 'externalReference'"
    )


def test_product_variant_bulk_create_will_create_new_attr_value_and_external_reference(
    staff_api_client,
    product,
    color_attribute,
    permission_manage_products,
):
    # given
    product.product_type.variant_attributes.add(color_attribute)
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_value = color_attribute.values.last()
    attribute_external_ref = color_attribute.external_reference
    sku = str(uuid4())[:12]
    color_attr_values_count = color_attribute.values.count()
    new_value = "NewColorValue"
    new_value_external_ref = attribute_value.external_reference + "New"

    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [
                {
                    "externalReference": attribute_external_ref,
                    "dropdown": {
                        "externalReference": new_value_external_ref,
                        "value": new_value,
                    },
                }
            ],
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
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    assert color_attribute.values.count() == color_attr_values_count + 1
    assert (
        data["results"][0]["productVariant"]["attributes"][1]["attribute"]["slug"]
        == color_attribute.slug
    )
    assert (
        data["results"][0]["productVariant"]["attributes"][1]["values"][0]["name"]
        == new_value
    )


def test_product_variant_bulk_create_with_swatch_attribute(
    staff_api_client, product, swatch_attribute, permission_manage_products
):
    # given
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

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert {result["productVariant"]["name"] for result in data["results"]} == {
        attribute_value_1.name,
        attribute_value_2.name,
    }
    assert product_variant_count + 2 == ProductVariant.objects.count()
    assert attribute_value_count == swatch_attribute.values.count()
    product_variant = ProductVariant.objects.get(sku=sku)
    product.refresh_from_db()
    assert product.default_variant == product_variant


def test_product_variant_bulk_create_with_plain_text_attribute(
    staff_api_client, product, plain_text_attribute, permission_manage_products
):
    # given
    product_variant_count = ProductVariant.objects.count()
    product.product_type.variant_attributes.add(plain_text_attribute)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", plain_text_attribute.pk)
    plain_text = "Test Text"
    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [{"id": attribute_id, "plainText": plain_text}],
        }
    ]

    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    attributes = data["results"][0]["productVariant"]["attributes"]
    assert attributes[-1]["values"][0]["plainText"] == plain_text
    assert product_variant_count + 1 == ProductVariant.objects.count()


@freeze_time(datetime(2020, 5, 5, 5, 5, 5, tzinfo=pytz.utc))
def test_product_variant_bulk_create_with_date_attribute(
    staff_api_client, product, date_attribute, permission_manage_products
):
    # given
    product_variant_count = ProductVariant.objects.count()
    product.product_type.variant_attributes.add(date_attribute)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", date_attribute.pk)
    date_time_value = datetime.now(tz=pytz.utc)
    date_value = date_time_value.date()

    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [{"id": attribute_id, "date": date_value}],
        }
    ]

    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    attributes = data["results"][0]["productVariant"]["attributes"]
    assert attributes[-1]["values"][0]["date"] == str(date_value)
    assert product_variant_count + 1 == ProductVariant.objects.count()


def test_product_variant_bulk_create_with_file_attribute(
    staff_api_client, product, file_attribute, permission_manage_products, site_settings
):
    # given
    product_variant_count = ProductVariant.objects.count()
    product.product_type.variant_attributes.add(file_attribute)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", file_attribute.pk)
    existing_value = file_attribute.values.first()
    domain = site_settings.site.domain
    file_url = f"http://{domain}{settings.MEDIA_URL}{existing_value.file_url}"

    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [{"id": attribute_id, "file": file_url}],
        }
    ]

    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    attributes = data["results"][0]["productVariant"]["attributes"]
    assert attributes[-1]["values"][0]["file"]["url"] == file_url
    assert product_variant_count + 1 == ProductVariant.objects.count()


@freeze_time(datetime(2020, 5, 5, 5, 5, 5, tzinfo=pytz.utc))
def test_product_variant_bulk_create_with_datetime_attribute(
    staff_api_client,
    product,
    date_time_attribute,
    permission_manage_products,
    site_settings,
):
    # given
    product_variant_count = ProductVariant.objects.count()
    product.product_type.variant_attributes.add(date_time_attribute)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", date_time_attribute.pk)
    date_time_value = datetime.now(tz=pytz.utc)

    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [{"id": attribute_id, "dateTime": date_time_value}],
        }
    ]

    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    attributes = data["results"][0]["productVariant"]["attributes"]
    assert attributes[-1]["values"][0]["dateTime"] == date_time_value.isoformat()
    assert product_variant_count + 1 == ProductVariant.objects.count()


def test_product_variant_bulk_create_with_rich_text_attribute(
    staff_api_client,
    product,
    rich_text_attribute,
    permission_manage_products,
    site_settings,
):
    # given
    product_variant_count = ProductVariant.objects.count()
    product.product_type.variant_attributes.add(rich_text_attribute)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", rich_text_attribute.pk)
    rich_text = json.dumps(dummy_editorjs("Sample text"))

    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [{"id": attribute_id, "richText": rich_text}],
        }
    ]

    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    attributes = data["results"][0]["productVariant"]["attributes"]
    assert attributes[-1]["values"][0]["richText"] == rich_text
    assert product_variant_count + 1 == ProductVariant.objects.count()


def test_product_variant_bulk_create_with_numeric_attribute(
    staff_api_client,
    product,
    numeric_attribute,
    permission_manage_products,
    site_settings,
):
    # given
    product_variant_count = ProductVariant.objects.count()
    product.product_type.variant_attributes.add(numeric_attribute)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", numeric_attribute.pk)
    existing_value = numeric_attribute.values.first()

    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [{"id": attribute_id, "values": [existing_value.name]}],
        }
    ]

    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    attributes = data["results"][0]["productVariant"]["attributes"]
    assert attributes[-1]["values"][0]["name"] == existing_value.name
    assert product_variant_count + 1 == ProductVariant.objects.count()


def test_product_variant_bulk_create_with_page_reference_attribute(
    staff_api_client,
    product,
    product_type_page_reference_attribute,
    permission_manage_products,
    site_settings,
    page,
):
    # given
    product_variant_count = ProductVariant.objects.count()
    product.product_type.variant_attributes.add(product_type_page_reference_attribute)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    reference_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.id
    )
    reference = graphene.Node.to_global_id("Page", page.pk)

    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [{"id": reference_attr_id, "references": [reference]}],
        }
    ]

    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    attributes = data["results"][0]["productVariant"]["attributes"]
    assert attributes[-1]["values"][0]["reference"] == reference
    assert product_variant_count + 1 == ProductVariant.objects.count()


def test_product_variant_bulk_create_with_dropdown_attribute(
    staff_api_client,
    product,
    size_attribute,
    permission_manage_products,
):
    # given
    product_variant_count = ProductVariant.objects.count()
    product.product_type.variant_attributes.add(size_attribute)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    attribute_value = size_attribute.values.last()
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.pk
    )
    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [
                {
                    "id": attribute_id,
                    "dropdown": {
                        "id": attribute_value_id,
                    },
                }
            ],
        }
    ]

    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    attributes = data["results"][0]["productVariant"]["attributes"]
    assert attributes[-1]["values"][0]["name"] == attribute_value.name
    assert product_variant_count + 1 == ProductVariant.objects.count()


def test_product_variant_bulk_create_with_multiselect_attribute(
    staff_api_client,
    product,
    size_attribute,
    permission_manage_products,
):
    # given
    product_variant_count = ProductVariant.objects.count()
    size_attribute.input_type = AttributeInputType.MULTISELECT
    size_attribute.save(update_fields=["input_type"])

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    attribute_value = size_attribute.values.last()
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.pk
    )
    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [
                {"id": attribute_id, "multiselect": [{"id": attribute_value_id}]},
            ],
        }
    ]

    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    attributes = data["results"][0]["productVariant"]["attributes"]
    assert attributes[-1]["values"][0]["name"] == attribute_value.name
    assert product_variant_count + 1 == ProductVariant.objects.count()


def test_product_variant_bulk_create_only_not_variant_selection_attributes(
    staff_api_client, product, size_attribute, permission_manage_products
):
    """Ensure that sku is set as variant name when only variant selection attributes
    are assigned.
    """

    # given
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

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    assert data["results"][0]["productVariant"]["name"] == sku
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
    assert not data["results"][0]["errors"]
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
    # given
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

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
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

    # given
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

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    assert product_variant_count + 1 == ProductVariant.objects.count()
    assert attribute_value_count == size_attribute.values.count()
    product_variant = ProductVariant.objects.get(sku=sku)
    product.refresh_from_db()
    assert product.default_variant == product_variant


def test_product_variant_bulk_create_attribute_with_blank_value(
    staff_api_client,
    product_with_single_variant,
    size_attribute,
    permission_manage_products,
):
    # given
    product = product_with_single_variant
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)

    variants = [
        {"sku": str(uuid4())[:12], "attributes": [{"id": attribute_id, "values": [""]}]}
    ]
    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert data["results"][0]["errors"]
    error = data["results"][0]["errors"][0]
    assert error["code"] == ProductVariantBulkErrorCode.REQUIRED.name
    assert error["field"] == "attributes"


def test_product_variant_bulk_create_stocks_input(
    staff_api_client, product, permission_manage_products, warehouses, size_attribute
):
    # given
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

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
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

    # then
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert product_variant_count + 2 == ProductVariant.objects.count()
    assert attribute_value_count + 1 == size_attribute.values.count()

    for result in data["results"]:
        variant_data = result["productVariant"]
        variant_data.pop("id")
        assert variant_data["sku"] in expected_result
        expected_variant = expected_result[variant_data["sku"]]
        expected_stocks = expected_variant["stocks"]
        assert all([stock in expected_stocks for stock in variant_data["stocks"]])


def test_product_variant_bulk_create_duplicated_warehouses(
    staff_api_client, product, permission_manage_products, warehouses, size_attribute
):
    # given
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

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    errors = data["results"][1]["errors"]

    # then
    assert not data["results"][0]["errors"]
    assert not data["results"][0]["productVariant"]
    assert not data["results"][1]["productVariant"]
    assert len(errors) == 2
    error = errors[0]
    assert error["field"] == "warehouse"
    assert error["path"] == "stocks.0.warehouse"
    assert error["code"] == ProductVariantBulkErrorCode.DUPLICATED_INPUT_ITEM.name
    assert error["warehouses"] == [warehouse1_id]


def test_product_variant_bulk_create_duplicated_warehouses_when_ignore_failed(
    staff_api_client, product, permission_manage_products, warehouses, size_attribute
):
    # given
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

    variables = {
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
        "productId": product_id,
        "variants": variants,
    }

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    errors = data["results"][1]["errors"]

    # then
    assert not data["results"][0]["errors"]
    assert data["results"][0]["productVariant"]
    assert data["results"][1]["productVariant"]
    assert not data["results"][1]["productVariant"]["stocks"]
    assert len(errors) == 2
    error = errors[0]
    assert error["field"] == "warehouse"
    assert error["path"] == "stocks.0.warehouse"
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
    # given
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

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
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

    # then
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert product_variant_count + 2 == ProductVariant.objects.count()
    assert attribute_value_count + 1 == size_attribute.values.count()

    for result in data["results"]:
        variant_data = result["productVariant"]
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

    # ensure all variants channel listings has discounted_price_amount set
    assert all(
        list(
            ProductVariantChannelListing.objects.values_list(
                "discounted_price_amount", flat=True
            )
        )
    )


def test_product_variant_bulk_create_preorder_channel_listings_input(
    staff_api_client,
    product_available_in_many_channels,
    permission_manage_products,
    size_attribute,
    channel_USD,
    channel_PLN,
):
    # given
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

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
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

    # then
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert product_variant_count + 2 == ProductVariant.objects.count()
    assert attribute_value_count + 1 == size_attribute.values.count()

    for result in data["results"]:
        variant_data = result["productVariant"]
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
    # given
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

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert len(data["results"][0]["errors"]) == 2
    error = data["results"][0]["errors"][0]
    assert error["path"] == "channelListings.0.channelId"
    assert error["code"] == ProductVariantBulkErrorCode.DUPLICATED_INPUT_ITEM.name
    assert error["channels"] == [channel_id]
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_duplicated_channels_when_ignore_failed(
    staff_api_client,
    product_available_in_many_channels,
    permission_manage_products,
    warehouses,
    size_attribute,
    channel_USD,
):
    # given
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

    variables = {
        "productId": product_id,
        "variants": variants,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert len(data["results"][0]["errors"]) == 2
    assert data["results"][0]["productVariant"]
    assert not data["results"][0]["productVariant"]["channelListings"]
    error = data["results"][0]["errors"][0]
    assert error["field"] == "channelId"
    assert error["path"] == "channelListings.0.channelId"
    assert error["code"] == ProductVariantBulkErrorCode.DUPLICATED_INPUT_ITEM.name
    assert error["channels"] == [channel_id]
    assert product_variant_count + 1 == ProductVariant.objects.count()


def test_product_variant_bulk_create_too_many_decimal_places_in_price(
    staff_api_client,
    product_available_in_many_channels,
    permission_manage_products,
    size_attribute,
    channel_USD,
    channel_PLN,
):
    # given
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

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    errors = data["results"][0]["errors"]
    assert len(errors) == 4
    assert errors[0]["field"] == "price"
    assert errors[0]["path"] == "channelListings.0.price"
    assert errors[0]["code"] == ProductVariantBulkErrorCode.INVALID_PRICE.name
    assert errors[0]["channels"] == [channel_id]
    assert errors[1]["field"] == "costPrice"
    assert errors[1]["path"] == "channelListings.0.costPrice"
    assert errors[1]["code"] == ProductVariantBulkErrorCode.INVALID_PRICE.name
    assert errors[1]["channels"] == [channel_id]
    assert errors[2]["field"] == "price"
    assert errors[2]["path"] == "channelListings.1.price"
    assert errors[2]["code"] == ProductVariantBulkErrorCode.INVALID_PRICE.name
    assert errors[2]["channels"] == [channel_pln_id]
    assert errors[3]["field"] == "costPrice"
    assert errors[3]["path"] == "channelListings.1.costPrice"
    assert errors[3]["code"] == ProductVariantBulkErrorCode.INVALID_PRICE.name
    assert errors[3]["channels"] == [channel_pln_id]
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_too_many_price_decimal_places_when_ignore_failed(
    staff_api_client,
    product_available_in_many_channels,
    permission_manage_products,
    size_attribute,
    channel_USD,
    channel_PLN,
):
    # given
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

    variables = {
        "productId": product_id,
        "variants": variants,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    errors = data["results"][0]["errors"]

    # then
    assert data["results"][0]["productVariant"]
    assert not data["results"][0]["productVariant"]["channelListings"]
    assert len(errors) == 4
    assert errors[0]["field"] == "price"
    assert errors[0]["code"] == ProductVariantBulkErrorCode.INVALID_PRICE.name
    assert errors[0]["channels"] == [channel_id]
    assert errors[1]["field"] == "costPrice"
    assert errors[1]["code"] == ProductVariantBulkErrorCode.INVALID_PRICE.name
    assert errors[1]["channels"] == [channel_id]
    assert errors[2]["field"] == "price"
    assert errors[2]["code"] == ProductVariantBulkErrorCode.INVALID_PRICE.name
    assert errors[2]["channels"] == [channel_pln_id]
    assert errors[3]["field"] == "costPrice"
    assert errors[3]["code"] == ProductVariantBulkErrorCode.INVALID_PRICE.name
    assert errors[3]["channels"] == [channel_pln_id]
    assert product_variant_count + 1 == ProductVariant.objects.count()


def test_product_variant_bulk_create_product_not_assigned_to_channel(
    staff_api_client,
    product,
    permission_manage_products,
    warehouses,
    size_attribute,
    channel_PLN,
):
    # given
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

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert len(data["results"][0]["errors"]) == 1
    error = data["results"][0]["errors"][0]
    code = ProductVariantBulkErrorCode.PRODUCT_NOT_ASSIGNED_TO_CHANNEL.name
    assert error["field"] == "channelId"
    assert error["code"] == code
    assert error["channels"] == [channel_id]
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_duplicated_sku(
    staff_api_client,
    product,
    product_with_default_variant,
    size_attribute,
    permission_manage_products,
):
    # given
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

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    input_1_errors = data["results"][0]["errors"]
    input_2_errors = data["results"][1]["errors"]
    assert input_1_errors
    assert input_2_errors
    assert input_1_errors[0]["field"] == "sku"
    assert input_1_errors[0]["code"] == ProductVariantBulkErrorCode.UNIQUE.name
    assert input_2_errors[0]["field"] == "sku"
    assert input_2_errors[0]["code"] == ProductVariantBulkErrorCode.UNIQUE.name
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_duplicated_sku_when_ignore_failed(
    staff_api_client,
    product,
    product_with_default_variant,
    size_attribute,
    permission_manage_products,
):
    # given
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

    variables = {
        "productId": product_id,
        "variants": variants,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    input_1_errors = data["results"][0]["errors"]
    input_2_errors = data["results"][1]["errors"]
    assert input_1_errors
    assert input_2_errors
    assert input_1_errors[0]["field"] == "sku"
    assert input_1_errors[0]["code"] == ProductVariantBulkErrorCode.UNIQUE.name
    assert input_2_errors[0]["field"] == "sku"
    assert input_2_errors[0]["code"] == ProductVariantBulkErrorCode.UNIQUE.name
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_duplicated_sku_in_input(
    staff_api_client, product, size_attribute, permission_manage_products
):
    # given
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

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    input_2_errors = data["results"][1]["errors"]
    assert data["results"][0]["errors"]
    assert len(input_2_errors) == 1
    assert input_2_errors[0]["field"] == "sku"
    assert input_2_errors[0]["code"] == ProductVariantBulkErrorCode.UNIQUE.name
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_duplicated_sku_in_input_when_ignore_failed(
    staff_api_client, product, size_attribute, permission_manage_products
):
    # given
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

    variables = {
        "productId": product_id,
        "variants": variants,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    input_1_errors = data["results"][0]["errors"]
    input_2_errors = data["results"][1]["errors"]
    assert not data["results"][0]["productVariant"]
    assert len(input_2_errors) == 1
    assert len(input_1_errors) == 1
    assert input_1_errors[0]["field"] == "sku"
    assert input_1_errors[0]["code"] == ProductVariantBulkErrorCode.UNIQUE.name
    assert input_2_errors[0]["field"] == "sku"
    assert input_2_errors[0]["code"] == ProductVariantBulkErrorCode.UNIQUE.name
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_without_sku(
    staff_api_client, product, size_attribute, permission_manage_products
):
    # given
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

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert product_variant_count + 2 == ProductVariant.objects.count()
    assert attribute_value_count + 1 == size_attribute.values.count()
    assert ProductVariant.objects.filter(sku__isnull=True).count() == 2


@patch("saleor.product.tasks.update_product_discounted_price_task.delay")
def test_product_variant_bulk_create_many_errors(
    update_product_discounted_price_task_mock,
    staff_api_client,
    product,
    size_attribute,
    permission_manage_products,
):
    # given
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

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    input_3_errors = data["results"][2]["errors"]
    input_4_errors = data["results"][3]["errors"]
    assert input_3_errors[0] == {
        "field": "sku",
        "path": "sku",
        "code": ProductVariantBulkErrorCode.UNIQUE.name,
        "message": ANY,
        "warehouses": None,
        "channels": None,
    }
    assert input_4_errors[0] == {
        "field": "attributes",
        "path": "attributes",
        "code": ProductVariantBulkErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED.name,
        "message": ANY,
        "warehouses": None,
        "channels": None,
    }
    assert product_variant_count == ProductVariant.objects.count()
    update_product_discounted_price_task_mock.assert_not_called()


def test_product_variant_bulk_create_many_errors_with_ignore_failed(
    staff_api_client, product, size_attribute, warehouses, permission_manage_products
):
    # given
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    non_existent_attribute_pk = 0
    invalid_attribute_id = graphene.Node.to_global_id(
        "Attribute", non_existent_attribute_pk
    )
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouses[0].pk)

    sku = product.variants.first().sku
    variants = [
        {
            "sku": str(uuid4())[:12],
            "attributes": [{"id": size_attribute_id, "values": ["Test-value1"]}],
            "stocks": [
                {"quantity": 15, "warehouse": warehouse_id},
                {"quantity": 15, "warehouse": warehouse_id},
            ],
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

    variables = {
        "productId": product_id,
        "variants": variants,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    input_3_errors = data["results"][2]["errors"]
    input_4_errors = data["results"][3]["errors"]
    assert input_3_errors[0] == {
        "field": "sku",
        "path": "sku",
        "code": ProductVariantBulkErrorCode.UNIQUE.name,
        "message": ANY,
        "warehouses": None,
        "channels": None,
    }
    assert input_4_errors[0] == {
        "field": "attributes",
        "path": "attributes",
        "code": ProductVariantBulkErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED.name,
        "message": ANY,
        "warehouses": None,
        "channels": None,
    }
    assert product_variant_count + 2 == ProductVariant.objects.count()


def test_product_variant_bulk_create_many_errors_with_reject_failed_rows(
    staff_api_client, product, size_attribute, warehouses, permission_manage_products
):
    # given
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    non_existent_attribute_pk = 0
    invalid_attribute_id = graphene.Node.to_global_id(
        "Attribute", non_existent_attribute_pk
    )
    sku = product.variants.first().sku
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouses[0].pk)

    variants = [
        {
            "sku": str(uuid4())[:12],
            "attributes": [{"id": size_attribute_id, "values": ["Test-value1"]}],
            "stocks": [
                {"quantity": 15, "warehouse": warehouse_id},
                {"quantity": 15, "warehouse": warehouse_id},
            ],
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

    variables = {
        "productId": product_id,
        "variants": variants,
        "errorPolicy": ErrorPolicyEnum.REJECT_FAILED_ROWS.name,
    }

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    input_3_errors = data["results"][2]["errors"]
    input_4_errors = data["results"][3]["errors"]
    assert input_3_errors[0] == {
        "field": "sku",
        "path": "sku",
        "code": ProductVariantBulkErrorCode.UNIQUE.name,
        "message": ANY,
        "warehouses": None,
        "channels": None,
    }

    assert input_4_errors[0] == {
        "field": "attributes",
        "path": "attributes",
        "code": ProductVariantBulkErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED.name,
        "message": ANY,
        "warehouses": None,
        "channels": None,
    }
    assert product_variant_count + 1 == ProductVariant.objects.count()


def test_product_variant_bulk_create_two_variants_duplicated_one_attribute_value(
    staff_api_client,
    product_with_variant_with_two_attributes,
    color_attribute,
    size_attribute,
    permission_manage_products,
):
    # given
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

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]

    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    assert product_variant_count + 1 == ProductVariant.objects.count()


def test_product_variant_bulk_create_with_default_track_inventory(
    staff_api_client,
    product_with_variant_with_two_attributes,
    permission_manage_products,
    site_settings,
):
    # given
    product = product_with_variant_with_two_attributes
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variants = [{"sku": str(uuid4())[:12], "attributes": []}]
    variables = {"productId": product_id, "variants": variants}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    # then
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    assert (
        data["results"][0]["productVariant"]["trackInventory"]
        == site_settings.track_inventory_by_default
    )
