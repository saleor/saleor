import json
from datetime import datetime, timedelta
from unittest.mock import ANY, patch
from uuid import uuid4

import graphene
import pytest
import pytz
from django.conf import settings
from django.utils.text import slugify

from .....attribute import AttributeInputType
from .....attribute.models import AttributeValue
from .....attribute.utils import associate_attribute_values_to_instance
from .....product.error_codes import ProductErrorCode
from .....tests.utils import flush_post_commit_hooks
from ....tests.utils import get_graphql_content


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
def test_update_product_variant_by_id(
    product_variant_updated_webhook_mock,
    product_variant_created_webhook_mock,
    staff_api_client,
    product,
    size_attribute,
    permission_manage_products,
):
    query = """
        mutation updateVariant (
            $id: ID!
            $sku: String!
            $quantityLimitPerCustomer: Int!
            $trackInventory: Boolean!
            $externalReference: String
            $attributes: [AttributeValueInput!]) {
                productVariantUpdate(
                    id: $id,
                    input: {
                        sku: $sku,
                        trackInventory: $trackInventory,
                        attributes: $attributes,
                        externalReference: $externalReference
                        quantityLimitPerCustomer: $quantityLimitPerCustomer,
                    }) {
                    productVariant {
                        name
                        sku
                        quantityLimitPerCustomer
                        externalReference
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
    external_reference = "test-ext-ref"

    variables = {
        "id": variant_id,
        "sku": sku,
        "trackInventory": True,
        "quantityLimitPerCustomer": quantity_limit_per_customer,
        "attributes": [{"id": attribute_id, "values": [attr_value]}],
        "externalReference": external_reference,
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
    assert data["externalReference"] == external_reference == variant.external_reference
    assert data["quantityLimitPerCustomer"] == quantity_limit_per_customer
    product_variant_updated_webhook_mock.assert_called_once_with(
        product.variants.last()
    )
    product_variant_created_webhook_mock.assert_not_called()


UPDATE_VARIANT_BY_SKU = """
 mutation updateVariant (
            $sku: String!,
            $newSku: String!,
            $quantityLimitPerCustomer: Int!
            $trackInventory: Boolean!,
            $attributes: [AttributeValueInput!]) {
                productVariantUpdate(
                    sku: $sku,
                    input: {
                        sku: $newSku,
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
                    errors {
                      field
                      message
                      attributes
                      code
                    }
                }
            }

"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_update_product_variant_by_sku(
    product_variant_updated_webhook_mock,
    product_variant_created_webhook_mock,
    staff_api_client,
    product,
    size_attribute,
    permission_manage_products,
):
    #   given
    variant = product.variants.first()
    attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    sku = "test sku"
    quantity_limit_per_customer = 5
    attr_value = "S"

    variables = {
        "sku": variant.sku,
        "newSku": sku,
        "trackInventory": True,
        "quantityLimitPerCustomer": quantity_limit_per_customer,
        "attributes": [{"id": attribute_id, "values": [attr_value]}],
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_VARIANT_BY_SKU, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantUpdate"]["productVariant"]

    # then
    assert data["name"] == variant.name
    assert data["sku"] == sku
    assert data["quantityLimitPerCustomer"] == quantity_limit_per_customer
    product_variant_updated_webhook_mock.assert_called_once_with(
        product.variants.last()
    )
    product_variant_created_webhook_mock.assert_not_called()


def test_update_product_variant_by_sku_return_error_when_sku_dont_exists(
    staff_api_client,
    product,
    size_attribute,
    permission_manage_products,
):
    # given
    variant = product.variants.first()
    attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    sku = "test sku"
    quantity_limit_per_customer = 5
    attr_value = "S"

    variables = {
        "sku": "randomSku",
        "newSku": sku,
        "trackInventory": True,
        "quantityLimitPerCustomer": quantity_limit_per_customer,
        "attributes": [{"id": attribute_id, "values": [attr_value]}],
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_VARIANT_BY_SKU, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantUpdate"]

    # then
    assert data["errors"][0]["field"] == "sku"
    assert data["errors"][0]["code"] == "NOT_FOUND"


UPDATE_VARIANT_BY_EXTERNAL_REFERENCE = """
     mutation updateVariant (
        $id: ID, $externalReference: String, $input: ProductVariantInput!
    ) {
        productVariantUpdate(
            id: $id,
            externalReference: $externalReference,
            input: $input
        ) {
            productVariant {
                id
                sku
                externalReference
            }
            errors {
              message
              field
              code
            }
        }
    }
    """


@patch("saleor.plugins.manager.PluginsManager.product_variant_created")
@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_update_product_variant_by_external_reference(
    product_variant_updated_webhook_mock,
    product_variant_created_webhook_mock,
    staff_api_client,
    product,
    size_attribute,
    permission_manage_products,
):
    #   given
    query = UPDATE_VARIANT_BY_EXTERNAL_REFERENCE

    ext_ref = "test-ext-ref"
    new_sku = "new-test-sku"
    variant = product.variants.first()
    variant.external_reference = ext_ref
    variant.save(update_fields=["external_reference"])

    variables = {
        "externalReference": ext_ref,
        "input": {"sku": new_sku},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantUpdate"]

    # then
    assert not data["errors"]
    assert data["productVariant"]["sku"] == new_sku
    assert data["productVariant"]["externalReference"] == ext_ref
    assert data["productVariant"]["id"] == graphene.Node.to_global_id(
        variant._meta.model.__name__, variant.id
    )
    product_variant_updated_webhook_mock.assert_called_once_with(
        product.variants.last()
    )
    product_variant_created_webhook_mock.assert_not_called()


def test_update_product_variant_by_both_id_and_external_reference(
    staff_api_client,
    product,
    permission_manage_products,
):
    #   given
    query = UPDATE_VARIANT_BY_EXTERNAL_REFERENCE
    variables = {"externalReference": "whatever", "id": "whatever", "input": {}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productVariantUpdate"]["errors"]
    assert (
        errors[0]["message"]
        == "Argument 'id' cannot be combined with 'external_reference'"
    )


def test_update_product_variant_by_external_reference_not_existing(
    staff_api_client,
    product,
    permission_manage_products,
):
    #   given
    query = UPDATE_VARIANT_BY_EXTERNAL_REFERENCE
    ext_ref = "non-existing-ext-ref"
    variables = {"externalReference": ext_ref, "input": {}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productVariantUpdate"]["errors"]
    assert errors[0]["message"] == f"Couldn't resolve to a node: {ext_ref}"


def test_update_product_variant_with_non_unique_external_reference(
    staff_api_client,
    product_list,
    permission_manage_products,
):
    #   given
    query = UPDATE_VARIANT_BY_EXTERNAL_REFERENCE
    ext_ref = "test-ext-ref"

    product_1 = product_list[0]
    variant_1 = product_1.variants.first()
    variant_1.external_reference = ext_ref
    variant_1.save(update_fields=["external_reference"])

    product_2 = product_list[1]
    variant_2 = product_2.variants.first()
    variant_2_id = graphene.Node.to_global_id("ProductVariant", variant_2.pk)

    variables = {"id": variant_2_id, "input": {"externalReference": ext_ref}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["productVariantUpdate"]["errors"][0]
    assert error["field"] == "externalReference"
    assert error["code"] == ProductErrorCode.UNIQUE.name
    assert (
        error["message"]
        == "Product variant with this External reference already exists."
    )


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
            {"id": color_attribute_id, "values": ["Red"]},
            {"id": size_attribute_id, "values": ["Small"]},
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


def test_update_product_variant_with_matching_slugs_different_values(
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
    color_new_value = "r.ed"
    size_new_value = "SmaLL"
    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": color_attribute_id, "values": [color_new_value]},
            {"id": size_attribute_id, "values": [size_new_value]},
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
    assert variant.attributes.first().values.first().slug == "red-2"
    assert variant.attributes.last().values.first().slug == "small-2"


def test_update_product_variant_with_value_that_matching_existing_slug(
    staff_api_client,
    product_with_variant_with_two_attributes,
    permission_manage_products,
):
    product = product_with_variant_with_two_attributes
    variant = product.variants.first()
    sku = str(uuid4())[:12]
    assert not variant.sku == sku

    attribute_1, attribute_2 = product.product_type.variant_attributes.all()

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    attribute_1_id = graphene.Node.to_global_id("Attribute", attribute_1.pk)
    attribute_2_id = graphene.Node.to_global_id("Attribute", attribute_2.pk)

    attr_1_values_count = attribute_1.values.count()
    attr_2_values_count = attribute_2.values.count()

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": attribute_1_id, "values": [attribute_1.values.first().slug]},
            {"id": attribute_2_id, "values": [attribute_2.values.first().slug]},
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
    assert attribute_1.values.count() == attr_1_values_count
    assert attribute_2.values.count() == attr_2_values_count
    assert len(data["productVariant"]["attributes"]) == 2
    for attr_data in data["productVariant"]["attributes"]:
        assert len(attr_data["values"]) == 1


def test_update_product_variant_with_value_that_matching_existing_name(
    staff_api_client,
    product_with_variant_with_two_attributes,
    permission_manage_products,
):
    product = product_with_variant_with_two_attributes
    variant = product.variants.first()
    sku = str(uuid4())[:12]
    assert not variant.sku == sku

    attribute_1, attribute_2 = product.product_type.variant_attributes.all()

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    attribute_1_id = graphene.Node.to_global_id("Attribute", attribute_1.pk)
    attribute_2_id = graphene.Node.to_global_id("Attribute", attribute_2.pk)

    attr_1_values_count = attribute_1.values.count()
    attr_2_values_count = attribute_2.values.count()

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": attribute_1_id, "values": [attribute_1.values.first().name]},
            {"id": attribute_2_id, "values": [attribute_2.values.first().name]},
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
    attribute_1.refresh_from_db()
    attribute_2.refresh_from_db()
    assert variant.sku == sku
    assert attribute_1.values.count() == attr_1_values_count
    assert attribute_2.values.count() == attr_2_values_count
    assert len(data["productVariant"]["attributes"]) == 2
    for attr_data in data["productVariant"]["attributes"]:
        assert len(attr_data["values"]) == 1


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
def test_update_variant_with_swatch_attribute_new_value_created(
    product_variant_updated,
    permission_manage_products,
    product,
    product_type,
    staff_api_client,
    warehouse,
    swatch_attribute,
):
    # given
    product_type.variant_attributes.add(swatch_attribute)
    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "123"
    swatch_attr_id = graphene.Node.to_global_id("Attribute", swatch_attribute.pk)

    value = "NEW"
    values_count = swatch_attribute.values.count()
    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {
                "id": swatch_attr_id,
                "swatch": {"value": value},
            }
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

    assert not content["errors"]
    assert data["sku"] == sku
    assert data["attributes"][-1]["attribute"]["slug"] == swatch_attribute.slug
    assert data["attributes"][-1]["values"][0]["name"] == value
    assert swatch_attribute.values.count() == values_count + 1
    product_variant_updated.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_update_variant_with_swatch_attribute_existing_value(
    product_variant_updated,
    permission_manage_products,
    product,
    product_type,
    staff_api_client,
    warehouse,
    swatch_attribute,
):
    # given
    product_type.variant_attributes.add(swatch_attribute)
    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "123"
    swatch_attr_id = graphene.Node.to_global_id("Attribute", swatch_attribute.pk)

    value = swatch_attribute.values.first()
    value_id = graphene.Node.to_global_id("AttributeValue", value.id)
    values_count = swatch_attribute.values.count()
    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {
                "id": swatch_attr_id,
                "swatch": {"id": value_id},
            }
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

    assert not content["errors"]
    assert data["sku"] == sku
    assert data["attributes"][-1]["attribute"]["slug"] == swatch_attribute.slug
    assert data["attributes"][-1]["values"][0]["name"] == value.name
    assert swatch_attribute.values.count() == values_count
    product_variant_updated.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_update_variant_with_swatch_attribute_use_values(
    product_variant_updated,
    permission_manage_products,
    product,
    product_type,
    staff_api_client,
    warehouse,
    swatch_attribute,
):
    # given
    product_type.variant_attributes.add(swatch_attribute)
    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "123"
    swatch_attr_id = graphene.Node.to_global_id("Attribute", swatch_attribute.pk)

    value = "NEW"
    values_count = swatch_attribute.values.count()
    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": swatch_attr_id, "values": [value]},
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

    assert not content["errors"]
    assert data["sku"] == sku
    assert data["attributes"][-1]["attribute"]["slug"] == swatch_attribute.slug
    assert data["attributes"][-1]["values"][0]["name"] == value
    assert swatch_attribute.values.count() == values_count + 1
    product_variant_updated.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_update_variant_with_swatch_attribute_no_values_given(
    product_variant_updated,
    permission_manage_products,
    product,
    product_type,
    staff_api_client,
    warehouse,
    swatch_attribute,
):
    # given
    product_type.variant_attributes.add(swatch_attribute)
    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "123"
    swatch_attr_id = graphene.Node.to_global_id("Attribute", swatch_attribute.pk)

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": swatch_attr_id},
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

    assert not content["errors"]
    assert data["sku"] == sku
    assert data["attributes"][-1]["attribute"]["slug"] == swatch_attribute.slug
    assert not data["attributes"][-1]["values"]


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
            {"id": color_attribute_id, "values": ["Red"]},
            {"id": size_attribute_id, "values": ["Big"]},
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
    site_settings,
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
    file_url = (
        f"http://{site_settings.site.domain}{settings.MEDIA_URL}{second_value.file_url}"
    )

    variables = {
        "id": variant_id,
        "sku": sku,
        "price": 15,
        "attributes": [{"id": file_attribute_id, "file": file_url}],
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
    site_settings,
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
    domain = site_settings.site.domain
    file_url = f"http://{domain}{settings.MEDIA_URL}{file_attr_value.file_url}"

    variables = {
        "id": variant_id,
        "price": 15,
        "attributes": [{"id": file_attribute_id, "file": file_url}],
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
    site_settings,
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
    domain = site_settings.site.domain
    file_url = f"http://{domain}{settings.MEDIA_URL}{existing_value.file_url}"

    variables = {
        "id": variant_id,
        "sku": sku,
        "price": 15,
        "attributes": [{"id": file_attribute_id, "file": file_url}],
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
    assert value_data["file"]["url"] == file_url
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


def test_update_product_variant_with_variant_reference_attribute(
    staff_api_client,
    product_list,
    product_type_variant_reference_attribute,
    permission_manage_products,
):
    # given
    product = product_list[0]
    variant_ref = product_list[1].variants.first()

    variant = product.variants.first()
    sku = str(uuid4())[:12]
    assert not variant.sku == sku

    product_type = product.product_type
    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(product_type_variant_reference_attribute)

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_variant_reference_attribute.pk
    )
    reference = graphene.Node.to_global_id("ProductVariant", variant_ref.pk)

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [{"id": ref_attribute_id, "references": [reference]}],
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
    assert not data["errors"]
    variant_data = data["productVariant"]
    assert variant_data
    assert variant_data["sku"] == sku
    assert len(variant_data["attributes"]) == 1
    assert (
        variant_data["attributes"][0]["attribute"]["slug"]
        == product_type_variant_reference_attribute.slug
    )
    assert len(variant_data["attributes"][0]["values"]) == 1
    assert (
        variant_data["attributes"][0]["values"][0]["slug"]
        == f"{variant.pk}_{variant_ref.pk}"
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


def test_update_product_variant_name(
    staff_api_client, product, permission_manage_products
):
    # given
    query = """
        mutation updateVariant (
            $id: ID!,
            $name: String
        ) {
            productVariantUpdate(
                id: $id,
                input: {
                    name: $name,
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
    new_name = "new-variant-name"
    variables = {"id": variant_id, "name": new_name}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]

    # then
    assert not data["errors"]
    assert data["productVariant"]["name"] == new_name


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
