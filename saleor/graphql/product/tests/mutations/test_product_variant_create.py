import json
from datetime import datetime, timedelta
from unittest.mock import ANY, patch
from uuid import uuid4

import graphene
import pytz
from django.conf import settings
from django.utils.text import slugify
from freezegun import freeze_time

from .....product.error_codes import ProductErrorCode
from .....tests.utils import dummy_editorjs, flush_post_commit_hooks
from ....core.enums import WeightUnitsEnum
from ....tests.utils import get_graphql_content

CREATE_VARIANT_MUTATION = """
      mutation createVariant ($input: ProductVariantCreateInput!) {
                productVariantCreate(input: $input) {
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
                        metadata {
                            key
                            value
                        }
                        privateMetadata {
                            key
                            value
                        }
                        externalReference
                    }
                }
            }

"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_create_variant_with_name(
    updated_webhook_mock,
    created_webhook_mock,
    staff_api_client,
    product,
    product_type,
    permission_manage_products,
    warehouse,
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    name = "test-name"
    weight = 10.22
    metadata_key = "md key"
    metadata_value = "md value"
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
    external_reference = "test-ext-ref"

    variables = {
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "name": name,
            "weight": weight,
            "attributes": [{"id": attribute_id, "values": [variant_value]}],
            "trackInventory": True,
            "metadata": [{"key": metadata_key, "value": metadata_value}],
            "privateMetadata": [{"key": metadata_key, "value": metadata_value}],
            "externalReference": external_reference,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VARIANT_MUTATION, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()

    # then
    assert not content["errors"]
    data = content["productVariant"]
    assert data["name"] == name
    assert data["sku"] == sku
    assert data["attributes"][0]["attribute"]["slug"] == variant_slug
    assert data["attributes"][0]["values"][0]["slug"] == variant_value
    assert data["weight"]["unit"] == WeightUnitsEnum.KG.name
    assert data["weight"]["value"] == weight
    assert len(data["stocks"]) == 1
    assert data["stocks"][0]["quantity"] == stocks[0]["quantity"]
    assert data["stocks"][0]["warehouse"]["slug"] == warehouse.slug
    assert data["metadata"][0]["key"] == metadata_key
    assert data["metadata"][0]["value"] == metadata_value
    assert data["privateMetadata"][0]["key"] == metadata_key
    assert data["privateMetadata"][0]["value"] == metadata_value
    assert data["externalReference"] == external_reference

    created_webhook_mock.assert_called_once_with(product.variants.last())
    updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_create_variant_without_name(
    updated_webhook_mock,
    created_webhook_mock,
    staff_api_client,
    product,
    product_type,
    permission_manage_products,
    warehouse,
):
    # given
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
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "weight": weight,
            "attributes": [{"id": attribute_id, "values": [variant_value]}],
            "trackInventory": True,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()

    # then
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
        "input": {
            "product": product_id,
            "sku": "1",
            "weight": 10.22,
            "attributes": [{"id": attribute_id, "values": [variant_value]}],
            "preorder": {
                "globalThreshold": global_threshold,
                "endDate": end_date,
            },
        }
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
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "weight": weight,
            "attributes": [],
            "trackInventory": True,
        }
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
    site_settings,
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    weight = 10.22

    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(file_attribute)
    file_attr_id = graphene.Node.to_global_id("Attribute", file_attribute.id)
    existing_value = file_attribute.values.first()
    domain = site_settings.site.domain
    file_url = f"http://{domain}{settings.MEDIA_URL}{existing_value.file_url}"

    values_count = file_attribute.values.count()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "weight": weight,
            "attributes": [{"id": file_attr_id, "file": file_url}],
            "trackInventory": True,
        }
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
        "input": {
            "product": product_id,
            "sku": "1",
            "stocks": [
                {
                    "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
                    "quantity": 20,
                }
            ],
            "weight": 10.22,
            "attributes": [
                {"id": boolean_attr_id, "boolean": True},
                {"id": size_attr_id, "values": ["XXXL"]},
            ],
            "trackInventory": True,
        }
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
    site_settings,
):
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    weight = 10.22

    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(file_attribute)
    file_attr_id = graphene.Node.to_global_id("Attribute", file_attribute.id)
    new_value = "new_value.txt"
    file_url = f"http://{site_settings.site.domain}{settings.MEDIA_URL}{new_value}"

    values_count = file_attribute.values.count()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "weight": weight,
            "attributes": [{"id": file_attr_id, "file": file_url}],
            "trackInventory": True,
        }
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
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "weight": weight,
            "attributes": [{"id": file_attr_id}],
            "trackInventory": True,
        }
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
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "attributes": [{"id": ref_attr_id, "references": [page_ref_1, page_ref_2]}],
            "trackInventory": True,
        }
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
    site_settings,
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
    file_url = f"http://{site_settings.site.domain}{settings.MEDIA_URL}test.jpg"

    values_count = product_type_page_reference_attribute.values.count()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "attributes": [{"id": ref_attr_id, "file": file_url}],
            "trackInventory": True,
        }
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
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "attributes": [
                {"id": ref_attr_id, "references": [product_ref_1, product_ref_2]}
            ],
            "trackInventory": True,
        }
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
    site_settings,
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
    file_url = f"http://{site_settings.site.domain}{settings.MEDIA_URL}test.jpg"

    values_count = product_type_product_reference_attribute.values.count()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "attributes": [{"id": ref_attr_id, "file": file_url}],
            "trackInventory": True,
        }
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
def test_create_variant_with_variant_reference_attribute(
    created_webhook_mock,
    staff_api_client,
    product,
    product_type,
    product_type_variant_reference_attribute,
    product_list,
    permission_manage_products,
    warehouse,
):
    # given
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"

    product_type_variant_reference_attribute.value_required = True
    product_type_variant_reference_attribute.save(update_fields=["value_required"])

    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(product_type_variant_reference_attribute)
    ref_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_variant_reference_attribute.id
    )

    variant_1 = product_list[0].variants.first()
    variant_2 = product_list[1].variants.first()
    variant_ref_1 = graphene.Node.to_global_id("ProductVariant", variant_1.pk)
    variant_ref_2 = graphene.Node.to_global_id("ProductVariant", variant_2.pk)

    values_count = product_type_variant_reference_attribute.values.count()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "attributes": [
                {"id": ref_attr_id, "references": [variant_ref_1, variant_ref_2]}
            ],
            "trackInventory": True,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()

    assert not content["errors"]
    data = content["productVariant"]
    assert data["sku"] == sku
    variant_id = data["id"]
    _, variant_pk = graphene.Node.from_global_id(variant_id)
    assert (
        data["attributes"][0]["attribute"]["slug"]
        == product_type_variant_reference_attribute.slug
    )
    expected_values = [
        {
            "slug": f"{variant_pk}_{variant_1.pk}",
            "file": None,
            "richText": None,
            "plainText": None,
            "reference": variant_ref_1,
            "name": f"{variant_1.product.name}: {variant_1.name}",
            "boolean": None,
            "date": None,
            "dateTime": None,
        },
        {
            "slug": f"{variant_pk}_{variant_2.pk}",
            "file": None,
            "richText": None,
            "plainText": None,
            "reference": variant_ref_2,
            "name": f"{variant_2.product.name}: {variant_2.name}",
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

    product_type_variant_reference_attribute.refresh_from_db()
    assert product_type_variant_reference_attribute.values.count() == values_count + 2

    created_webhook_mock.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
def test_create_variant_with_variant_reference_attribute_no_references_given(
    created_webhook_mock,
    updated_webhook_mock,
    staff_api_client,
    product,
    product_type,
    product_type_variant_reference_attribute,
    permission_manage_products,
    warehouse,
    site_settings,
):
    # given
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"

    product_type_variant_reference_attribute.value_required = True
    product_type_variant_reference_attribute.save(update_fields=["value_required"])

    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(product_type_variant_reference_attribute)
    ref_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_variant_reference_attribute.id
    )

    values_count = product_type_variant_reference_attribute.values.count()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]
    file_url = f"http://{site_settings.site.domain}{settings.MEDIA_URL}test.jpg"

    variables = {
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "attributes": [{"id": ref_attr_id, "file": file_url}],
            "trackInventory": True,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    flush_post_commit_hooks()
    errors = content["errors"]
    data = content["productVariant"]

    assert not data
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [ref_attr_id]

    product_type_variant_reference_attribute.refresh_from_db()
    assert product_type_variant_reference_attribute.values.count() == values_count

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
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "weight": weight,
            "attributes": [{"id": attribute_id, "values": [variant_value]}],
            "trackInventory": True,
        }
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
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "weight": weight,
            "attributes": [{"id": attribute_id, "values": [variant_value]}],
            "trackInventory": True,
        }
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
        "input": {
            "product": product_id,
            "weight": -1,
            "attributes": [{"id": attribute_id, "values": [variant_value]}],
        }
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
        "input": {
            "product": product_id,
            "sku": "test-sku",
            "attributes": [],
        }
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
        "input": {
            "product": product_id,
            "sku": sku,
            "attributes": [{"id": attribute_id, "values": [variant_value]}],
        }
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
        "input": {
            "product": product_id,
            "sku": sku,
            "attributes": [
                {"id": color_attribute_id, "values": ["red"]},
                {"id": size_attribute_id, "values": ["small"]},
            ],
        }
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
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "weight": weight,
            "attributes": [
                {"id": color_attr_id, "values": [" "]},
                {"id": weight_attr_id, "values": [" "]},
                {
                    "id": size_attr_id,
                    "values": [non_existent_attr_value, size_value_slug],
                },
                {"id": rich_text_attr_id, "richText": json.dumps(dummy_editorjs(" "))},
            ],
            "trackInventory": True,
        }
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
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "weight": weight,
            "attributes": [
                {"id": attr_id, "richText": rich_text},
            ],
            "trackInventory": True,
        }
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
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "weight": weight,
            "attributes": [
                {"id": attr_id, "plainText": text},
            ],
            "trackInventory": True,
        }
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
    weight = 10.22
    date_attribute_id = graphene.Node.to_global_id("Attribute", date_attribute.id)
    date_time_value = datetime.now(tz=pytz.utc)
    date_value = date_time_value.date()

    variables = {
        "input": {
            "product": product_id,
            "sku": sku,
            "weight": weight,
            "attributes": [
                {"id": date_attribute_id, "date": date_value},
            ],
        }
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
    weight = 10.22
    date_time_attribute_id = graphene.Node.to_global_id(
        "Attribute", date_time_attribute.id
    )
    date_time_value = datetime.now(tz=pytz.utc)

    variables = {
        "input": {
            "product": product_id,
            "sku": sku,
            "weight": weight,
            "attributes": [
                {"id": date_time_attribute_id, "dateTime": date_time_value},
            ],
        }
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
        "input": {
            "product": product_id,
            "sku": sku,
            "stocks": stocks,
            "weight": weight,
            "attributes": [{"id": attribute_id, "values": [variant_value]}],
            "trackInventory": True,
        }
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
        "input": {
            "product": product_id,
            "stocks": stocks,
            "weight": weight,
            "attributes": [{"id": attribute_id, "values": [variant_value]}],
            "trackInventory": True,
        }
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


def test_create_product_variant_with_non_unique_external_reference(
    staff_api_client,
    category,
    product,
    product_type,
    permission_manage_products,
):
    # given
    query = CREATE_VARIANT_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variant = product.variants.first()
    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().pk
    )

    ext_ref = "test-ext-ref"
    variant.external_reference = ext_ref
    variant.save(update_fields=["external_reference"])

    variables = {
        "input": {
            "product": product_id,
            "attributes": [{"id": attribute_id, "values": ["test-value"]}],
            "externalReference": ext_ref,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["productVariantCreate"]["errors"][0]
    assert error["field"] == "externalReference"
    assert error["code"] == ProductErrorCode.UNIQUE.name
    assert (
        error["message"]
        == "Product variant with this External reference already exists."
    )
