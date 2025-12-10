import datetime
import json
from unittest.mock import ANY, patch
from uuid import uuid4

import graphene
import pytest
from django.conf import settings
from django.utils.text import slugify
from measurement.measures import Weight

from .....attribute import AttributeInputType
from .....attribute.models import AttributeValue
from .....attribute.utils import associate_attribute_values_to_instance
from .....product.error_codes import ProductErrorCode
from ....core.utils import snake_to_camel_case
from ....tests.utils import get_graphql_content
from ...mutations.product_variant.product_variant_create import ProductVariantInput


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
              assignedAttributes(limit:10) {
                  ... on AssignedSingleChoiceAttribute {
                        attribute {
                            slug
                        }
                        choice: value {
                            name
                            slug
                        }
                  }
              }
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

    assigned_attributes = data["productVariant"]["assignedAttributes"]
    expected_assigned_choice_attribute = {
        "attribute": {"slug": size_attribute.slug},
        "choice": {
            "name": attr_value,
            "slug": attr_value.lower(),
        },
    }
    assert expected_assigned_choice_attribute in assigned_attributes


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
    data = content["data"]["productVariantUpdate"]["productVariant"]

    assert data["name"] == variant.name
    assert data["sku"] == sku
    assert data["externalReference"] == external_reference == variant.external_reference
    assert data["quantityLimitPerCustomer"] == quantity_limit_per_customer
    product_variant_updated_webhook_mock.assert_called_once_with(
        product.variants.last()
    )
    product_variant_created_webhook_mock.assert_not_called()


def test_update_product_variant_marks_prices_as_dirty(
    staff_api_client,
    product,
    size_attribute,
    permission_manage_products,
    catalogue_promotion,
):
    # given
    query = """
        mutation updateVariant (
            $id: ID!
            $sku: String!) {
                productVariantUpdate(
                    id: $id,
                    input: {
                        sku: $sku,
                    }) {
                    productVariant {
                        name
                        sku
                    }
                }
            }
    """
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "test sku"

    variables = {
        "id": variant_id,
        "sku": sku,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    variant.refresh_from_db()
    get_graphql_content(response)
    assert not catalogue_promotion.rules.filter(variants_dirty=False).exists()


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
mutation updateVariant($id: ID!, $sku: String, $attributes: [AttributeValueInput!]) {
  productVariantUpdate(id: $id, input: {sku: $sku, attributes: $attributes}) {
    productVariant {
      sku
      assignedAttributes(limit:10) {
        attribute {
          slug
        }
        ... on AssignedNumericAttribute {
          value
        }
        ... on AssignedTextAttribute {
          text: value
        }
        ... on AssignedPlainTextAttribute {
          plain_text: value
        }
        ... on AssignedFileAttribute {
          file: value {
            contentType
            url
          }
        }
        ... on AssignedMultiPageReferenceAttribute {
          pages: value {
            slug
          }
        }
        ... on AssignedMultiProductReferenceAttribute {
          products: value {
            slug
          }
        }
        ... on AssignedMultiCategoryReferenceAttribute {
          categories: value {
            slug
          }
        }
        ... on AssignedMultiCollectionReferenceAttribute {
          collections: value {
            slug
          }
        }
        ... on AssignedSinglePageReferenceAttribute {
          page: value {
            slug
          }
        }
        ... on AssignedSingleProductReferenceAttribute {
          product: value {
            slug
          }
        }
        ... on AssignedSingleProductVariantReferenceAttribute {
          variant: value {
            sku
          }
        }
        ... on AssignedSingleCategoryReferenceAttribute {
          category: value {
            slug
          }
        }
        ... on AssignedSingleCollectionReferenceAttribute {
          collection: value {
            slug
          }
        }
        ... on AssignedMultiProductVariantReferenceAttribute {
          variants: value {
            sku
          }
        }
        ... on AssignedSingleChoiceAttribute {
          choice: value {
            name
            slug
          }
        }
        ... on AssignedMultiChoiceAttribute {
          multi: value {
            name
            slug
          }
        }
        ... on AssignedSwatchAttribute {
          swatch: value {
            name
            slug
            hexColor
            file {
              url
              contentType
            }
          }
        }
        ... on AssignedBooleanAttribute {
          bool: value
        }
        ... on AssignedDateAttribute {
          date: value
        }
        ... on AssignedDateTimeAttribute {
          datetime: value
        }
      }
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
      attributes
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
    assert len(data["productVariant"]["assignedAttributes"]) == 1


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
    assert attribute_1.input_type == AttributeInputType.DROPDOWN
    assert attribute_2.input_type == AttributeInputType.DROPDOWN

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    attribute_1_id = graphene.Node.to_global_id("Attribute", attribute_1.pk)
    attribute_2_id = graphene.Node.to_global_id("Attribute", attribute_2.pk)

    attr_1_values_count = attribute_1.values.count()
    attr_2_values_count = attribute_2.values.count()

    value_for_attr_1 = attribute_1.values.first()
    value_for_attr_2 = attribute_2.values.first()
    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": attribute_1_id, "values": [value_for_attr_1.slug]},
            {"id": attribute_2_id, "values": [value_for_attr_2.slug]},
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

    assigned_attributes = data["productVariant"]["assignedAttributes"]
    expected_first_assigned_choice_attribute = {
        "attribute": {"slug": attribute_1.slug},
        "choice": {
            "name": value_for_attr_1.name,
            "slug": value_for_attr_1.slug,
        },
    }
    expected_second_assigned_choice_attribute = {
        "attribute": {"slug": attribute_2.slug},
        "choice": {
            "name": value_for_attr_2.name,
            "slug": value_for_attr_2.slug,
        },
    }
    assert expected_first_assigned_choice_attribute in assigned_attributes
    assert expected_second_assigned_choice_attribute in assigned_attributes


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
    assert attribute_1.input_type == AttributeInputType.DROPDOWN
    assert attribute_2.input_type == AttributeInputType.DROPDOWN

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    attribute_1_id = graphene.Node.to_global_id("Attribute", attribute_1.pk)
    attribute_2_id = graphene.Node.to_global_id("Attribute", attribute_2.pk)

    attr_1_values_count = attribute_1.values.count()
    attr_2_values_count = attribute_2.values.count()

    value_for_attr_1 = attribute_1.values.first()
    value_for_attr_2 = attribute_2.values.first()

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": attribute_1_id, "values": [value_for_attr_1.name]},
            {"id": attribute_2_id, "values": [value_for_attr_2.name]},
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

    assigned_attributes = data["productVariant"]["assignedAttributes"]
    expected_first_assigned_choice_attribute = {
        "attribute": {"slug": attribute_1.slug},
        "choice": {
            "name": value_for_attr_1.name,
            "slug": value_for_attr_1.slug,
        },
    }
    expected_second_assigned_choice_attribute = {
        "attribute": {"slug": attribute_2.slug},
        "choice": {
            "name": value_for_attr_2.name,
            "slug": value_for_attr_2.slug,
        },
    }
    assert expected_first_assigned_choice_attribute in assigned_attributes
    assert expected_second_assigned_choice_attribute in assigned_attributes


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

    size_value_name = "XXXL"
    new_value = False
    values_count = boolean_attribute.values.count()
    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": size_attr_id, "values": [size_value_name]},
            {"id": attr_id, "boolean": new_value},
        ],
    }

    associate_attribute_values_to_instance(
        variant,
        {boolean_attribute.id: [boolean_attribute.values.first()]},
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

    assigned_attributes = data["assignedAttributes"]
    expected_boolean_assigned_choice_attribute = {
        "attribute": {"slug": boolean_attribute.slug},
        "bool": new_value,
    }
    expected_size_assigned_choice_attribute = {
        "attribute": {"slug": size_attribute.slug},
        "choice": {
            "name": size_value_name,
            "slug": size_value_name.lower(),
        },
    }
    assert expected_boolean_assigned_choice_attribute in assigned_attributes
    assert expected_size_assigned_choice_attribute in assigned_attributes

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

    assigned_attributes = data["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": swatch_attribute.slug},
        "swatch": {
            "name": value,
            "slug": slugify(value),
            "hexColor": None,
            "file": None,
        },
    }
    assert expected_assigned_attribute in assigned_attributes

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

    assigned_attributes = data["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": swatch_attribute.slug},
        "swatch": {
            "name": value.name,
            "slug": value.slug,
            "hexColor": value.value,
            "file": None,
        },
    }
    assert expected_assigned_attribute in assigned_attributes

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

    assigned_attributes = data["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": swatch_attribute.slug},
        "swatch": {
            "name": value,
            "slug": slugify(value),
            "hexColor": None,
            "file": None,
        },
    }
    assert expected_assigned_attribute in assigned_attributes

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

    assigned_attributes = data["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": swatch_attribute.slug},
        "swatch": None,
    }
    assert expected_assigned_attribute in assigned_attributes


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
    rich_text = rich_text_attribute_value.rich_text
    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": attr_id, "richText": json.dumps(rich_text)},
        ],
    }
    rich_text_attribute_value.slug = f"{variant.id}_{rich_text_attribute.id}"
    rich_text_attribute_value.save()
    values_count = rich_text_attribute.values.count()
    associate_attribute_values_to_instance(
        variant, {rich_text_attribute.id: [rich_text_attribute_value]}
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
    assert data["attributes"][-1]["values"][0]["richText"] == json.dumps(rich_text)

    assigned_attributes = data["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": rich_text_attribute.slug},
        "text": rich_text,
    }
    assert expected_assigned_attribute in assigned_attributes

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
        variant, {plain_text_attribute.id: [plain_text_attribute_value]}
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

    assigned_attributes = data["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": plain_text_attribute.slug},
        "plain_text": text,
    }
    assert expected_assigned_attribute in assigned_attributes

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
        variant, {plain_text_attribute.id: [plain_text_attribute_value]}
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

    assigned_attributes = data["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": plain_text_attribute.slug},
        "plain_text": text,
    }
    assert expected_assigned_attribute in assigned_attributes

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
        variant, {plain_text_attribute.id: [plain_text_attribute_value]}
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
    date_time_value = datetime.datetime(2025, 5, 5, 5, 5, 5, tzinfo=datetime.UTC)
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

    assigned_attributes = data["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": date_attribute.slug},
        "date": str(date_value),
    }
    assert expected_assigned_attribute in assigned_attributes

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
    date_time_value = datetime.datetime(2025, 5, 5, 5, 5, 5, tzinfo=datetime.UTC)
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

    assigned_attributes = data["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": date_time_attribute.slug},
        "datetime": date_time_value.isoformat(),
    }
    assert expected_assigned_attribute in assigned_attributes

    product_variant_updated.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_update_variant_removes_numeric_attribute_value(
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
    associate_attribute_values_to_instance(
        variant, {numeric_attribute.id: [attribute_value]}
    )

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

    assigned_attributes = data["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": numeric_attribute.slug},
        "value": None,
    }
    assert expected_assigned_attribute in assigned_attributes

    assert numeric_attribute.values.count() == values_count
    product_variant_updated.assert_called_once_with(product.variants.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_update_variant_adds_numeric_attribute(
    product_variant_updated,
    permission_manage_products,
    product,
    product_type,
    staff_api_client,
    numeric_attribute,
    warehouse,
):
    # given
    product_type.variant_attributes.add(numeric_attribute)

    numeric_value = 33.12
    numeric_name = str(numeric_value)

    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    attr_id = graphene.Node.to_global_id("Attribute", numeric_attribute.id)
    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variables = {
        "id": variant_id,
        "attributes": [
            {"id": attr_id, "numeric": numeric_name},
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

    attribute_data = [
        attr_data
        for attr_data in data["attributes"]
        if attr_data["attribute"]["slug"] == numeric_attribute.slug
    ][0]
    assert attribute_data["attribute"]["slug"] == numeric_attribute.slug
    assert attribute_data["values"][0]["name"] == numeric_name

    assigned_attributes = data["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": numeric_attribute.slug},
        "value": numeric_value,
    }
    assert expected_assigned_attribute in assigned_attributes

    assert numeric_attribute.values.filter(
        name=numeric_name, numeric=numeric_value
    ).first()
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
    assigned_attributes = data["productVariant"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": attribute.slug},
        "multi": [],
    }
    assert expected_assigned_attribute in assigned_attributes

    with pytest.raises(variant_attr._meta.model.DoesNotExist):
        variant_attr.refresh_from_db()


def test_update_product_variant_with_existing_values(
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
        variant2,
        {
            color_attribute.id: [color_attribute.values.last()],
            size_attribute.id: [size_attribute.values.last()],
        },
    )

    assert variant.attributes.first().values.first().slug == "red"
    assert variant.attributes.last().values.first().slug == "small"
    assert variant2.attributes.first().values.first().slug == "blue"
    assert variant2.attributes.last().values.first().slug == "big"

    color_attr_values_count = color_attribute.values.count()
    size_attr_values_count = size_attribute.values.count()

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
    errors = data["errors"]
    assert not errors
    variant_data = data["productVariant"]
    assert variant_data
    assert len(variant_data["attributes"]) == 2
    color_attribute.refresh_from_db()
    size_attribute.refresh_from_db()
    assert color_attribute.values.count() == color_attr_values_count
    assert size_attribute.values.count() == size_attr_values_count


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
    file_url = f"https://example.com{settings.MEDIA_URL}{second_value.file_url}"

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

    assigned_attributes = variant_data["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": file_attribute.slug},
        "file": {
            "url": file_url,
            "contentType": None,
        },
    }
    assert expected_assigned_attribute in assigned_attributes


def test_update_product_variant_with_existing_file_attribute(
    staff_api_client,
    product_with_variant_with_file_attribute,
    file_attribute,
    permission_manage_products,
):
    product = product_with_variant_with_file_attribute
    variant = product.variants.first()
    file_attr_value = file_attribute.values.last()
    associate_attribute_values_to_instance(
        variant, {file_attribute.id: [file_attr_value]}
    )

    sku = str(uuid4())[:12]

    values_count = file_attribute.values.count()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    file_attribute_id = graphene.Node.to_global_id("Attribute", file_attribute.pk)
    file_url = f"https://example.com{settings.MEDIA_URL}{file_attr_value.file_url}"

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
    assert not data["errors"]
    variant_data = data["productVariant"]
    assert variant_data
    assert len(variant_data["attributes"]) == 1
    file_attribute.refresh_from_db()
    assert file_attribute.values.count() == values_count


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
    file_url = f"https://example.com{settings.MEDIA_URL}{existing_value.file_url}"

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

    assigned_attributes = variant_data["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": file_attribute.slug},
        "file": {
            "url": file_url,
            "contentType": existing_value.content_type,
        },
    }
    assert expected_assigned_attribute in assigned_attributes


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

    assigned_attributes = variant_data["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": product_type_page_reference_attribute.slug},
        "pages": [
            {"slug": page.slug},
        ],
    }
    assert expected_assigned_attribute in assigned_attributes


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

    assigned_attributes = variant_data["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": product_type_product_reference_attribute.slug},
        "products": [{"slug": product_ref.slug}],
    }
    assert expected_assigned_attribute in assigned_attributes


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

    assigned_attributes = variant_data["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": product_type_variant_reference_attribute.slug},
        "variants": [{"sku": variant_ref.sku}],
    }
    assert expected_assigned_attribute in assigned_attributes


def test_update_product_variant_with_category_reference_attribute(
    staff_api_client,
    product,
    category,
    product_type_category_reference_attribute,
    permission_manage_products,
):
    # given
    variant = product.variants.first()
    sku = str(uuid4())[:12]
    assert not variant.sku == sku

    product_type = product.product_type
    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(product_type_category_reference_attribute)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_category_reference_attribute.pk
    )
    reference = graphene.Node.to_global_id("Category", category.pk)

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
        == product_type_category_reference_attribute.slug
    )
    assert len(variant_data["attributes"][0]["values"]) == 1
    assert (
        variant_data["attributes"][0]["values"][0]["slug"]
        == f"{variant.pk}_{category.pk}"
    )
    assert variant_data["attributes"][0]["values"][0]["reference"] == reference

    assigned_attributes = variant_data["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": product_type_category_reference_attribute.slug},
        "categories": [
            {"slug": category.slug},
        ],
    }
    assert expected_assigned_attribute in assigned_attributes


def test_update_product_variant_with_reference_attributes_and_reference_types_defined(
    staff_api_client,
    product_list,
    page,
    product_type_page_reference_attribute,
    product_type_product_reference_attribute,
    product_type_variant_reference_attribute,
    permission_manage_products,
):
    # given
    variant = product_list[0].variants.first()
    sku = str(uuid4())[:12]
    assert not variant.sku == sku

    product_type = variant.product.product_type
    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(
        product_type_page_reference_attribute,
        product_type_product_reference_attribute,
        product_type_variant_reference_attribute,
    )

    reference_product = product_list[1]
    reference_variant = product_list[2].variants.first()
    product_type_page_reference_attribute.reference_page_types.add(page.page_type)
    product_type_product_reference_attribute.reference_product_types.add(
        reference_product.product_type
    )
    product_type_variant_reference_attribute.reference_product_types.add(
        variant.product.product_type
    )

    page_ref_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.id
    )
    product_ref_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.id
    )
    variant_ref_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_variant_reference_attribute.id
    )
    variant_ref = graphene.Node.to_global_id("ProductVariant", reference_variant.pk)
    page_ref = graphene.Node.to_global_id("Page", page.pk)
    product_ref = graphene.Node.to_global_id("Product", reference_product.pk)

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": page_ref_attr_id, "references": [page_ref]},
            {"id": product_ref_attr_id, "references": [product_ref]},
            {"id": variant_ref_attr_id, "references": [variant_ref]},
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
    assert not data["errors"]
    variant_data = data["productVariant"]
    assert variant_data["sku"] == sku
    assert len(variant_data["attributes"]) == len(variables["attributes"])
    expected_attributes_data = [
        {
            "attribute": {"slug": product_type_page_reference_attribute.slug},
            "values": [
                {
                    "id": ANY,
                    "slug": f"{variant.pk}_{page.id}",
                    "file": None,
                    "richText": None,
                    "plainText": None,
                    "reference": page_ref,
                    "name": page.title,
                    "boolean": None,
                    "date": None,
                    "dateTime": None,
                }
            ],
        },
        {
            "attribute": {"slug": product_type_product_reference_attribute.slug},
            "values": [
                {
                    "id": ANY,
                    "slug": f"{variant.pk}_{reference_product.id}",
                    "file": None,
                    "richText": None,
                    "plainText": None,
                    "reference": product_ref,
                    "name": reference_product.name,
                    "boolean": None,
                    "date": None,
                    "dateTime": None,
                }
            ],
        },
        {
            "attribute": {"slug": product_type_variant_reference_attribute.slug},
            "values": [
                {
                    "id": ANY,
                    "slug": f"{variant.pk}_{reference_variant.id}",
                    "file": None,
                    "richText": None,
                    "plainText": None,
                    "reference": variant_ref,
                    "name": f"{reference_variant.product.name}: {reference_variant.name}",
                    "boolean": None,
                    "date": None,
                    "dateTime": None,
                }
            ],
        },
    ]
    for attr_data in variant_data["attributes"]:
        assert attr_data in expected_attributes_data

    assigned_attributes = variant_data["assignedAttributes"]
    expected_page_ref_assigned_attribute = {
        "attribute": {"slug": product_type_page_reference_attribute.slug},
        "pages": [{"slug": page.slug}],
    }
    assert expected_page_ref_assigned_attribute in assigned_attributes
    expected_product_ref_assigned_attribute = {
        "attribute": {"slug": product_type_product_reference_attribute.slug},
        "products": [{"slug": reference_product.slug}],
    }
    assert expected_product_ref_assigned_attribute in assigned_attributes
    expected_variant_ref_assigned_attribute = {
        "attribute": {"slug": product_type_variant_reference_attribute.slug},
        "variants": [{"sku": reference_variant.sku}],
    }
    assert expected_variant_ref_assigned_attribute in assigned_attributes


def test_update_product_variant_with_single_reference_attributes(
    staff_api_client,
    product,
    page,
    product_type_page_single_reference_attribute,
    product_type_product_single_reference_attribute,
    product_type_variant_single_reference_attribute,
    product_type_category_single_reference_attribute,
    product_type_collection_single_reference_attribute,
    permission_manage_products,
    collection,
    product_variant_list,
    categories,
):
    variant = product.variants.first()
    sku = str(uuid4())[:12]
    assert not variant.sku == sku

    product_type = product.product_type
    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(
        product_type_page_single_reference_attribute,
        product_type_product_single_reference_attribute,
        product_type_variant_single_reference_attribute,
        product_type_category_single_reference_attribute,
        product_type_collection_single_reference_attribute,
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    references = [
        (page, product_type_page_single_reference_attribute, page.title),
        (product, product_type_product_single_reference_attribute, product.name),
        (
            product_variant_list[0],
            product_type_variant_single_reference_attribute,
            f"{product_variant_list[0].product.name}: {product_variant_list[0].name}",
        ),
        (
            categories[0],
            product_type_category_single_reference_attribute,
            categories[0].name,
        ),
        (
            collection,
            product_type_collection_single_reference_attribute,
            collection.name,
        ),
    ]
    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", attr.pk),
            "reference": graphene.Node.to_global_id(attr.entity_type, ref.pk),
        }
        for ref, attr, _name in references
    ]

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": attributes,
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
    attributes_data = variant_data["attributes"]
    assert len(attributes_data) == len(references)
    expected_attributes_data = [
        {
            "attribute": {
                "slug": attr.slug,
            },
            "values": [
                {
                    "id": ANY,
                    "date": None,
                    "dateTime": None,
                    "richText": None,
                    "slug": f"{variant.id}_{ref.id}",
                    "name": name,
                    "file": None,
                    "plainText": None,
                    "boolean": None,
                    "reference": graphene.Node.to_global_id(attr.entity_type, ref.pk),
                }
            ],
        }
        for ref, attr, name in references
    ]
    for attr_data in attributes_data:
        assert attr_data in expected_attributes_data

    assigned_attributes = variant_data["assignedAttributes"]

    expected_assigned_page_attribute = {
        "attribute": {"slug": product_type_page_single_reference_attribute.slug},
        "page": {"slug": page.slug},
    }
    expected_assigned_product_attribute = {
        "attribute": {"slug": product_type_product_single_reference_attribute.slug},
        "product": {"slug": product.slug},
    }
    expected_assigned_variant_attribute = {
        "attribute": {"slug": product_type_variant_single_reference_attribute.slug},
        "variant": {"sku": product_variant_list[0].sku},
    }
    expected_assigned_category_attribute = {
        "attribute": {"slug": product_type_category_single_reference_attribute.slug},
        "category": {"slug": categories[0].slug},
    }
    expected_assigned_collection_attribute = {
        "attribute": {"slug": product_type_collection_single_reference_attribute.slug},
        "collection": {"slug": collection.slug},
    }
    assert expected_assigned_page_attribute in assigned_attributes
    assert expected_assigned_product_attribute in assigned_attributes
    assert expected_assigned_variant_attribute in assigned_attributes
    assert expected_assigned_category_attribute in assigned_attributes
    assert expected_assigned_collection_attribute in assigned_attributes


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
        {
            product_type_product_reference_attribute.id: [
                attr_value_3,
                attr_value_2,
                attr_value_1,
            ]
        },
    )

    assert list(
        variant.attributes.first().variantvalueassignment.values_list(
            "value_id", flat=True
        )
    ) == [attr_value_3.pk, attr_value_2.pk, attr_value_1.pk]

    expected_first_product = product_list[1]
    expected_second_product = product_list[0]
    expected_third_product = product_list[2]

    new_ref_order = [
        expected_first_product,
        expected_second_product,
        expected_third_product,
    ]

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
    assigned_attributes = data["productVariant"]["assignedAttributes"]
    assert len(assigned_attributes) == 1
    assigned_values = assigned_attributes[0]["products"]
    assert len(assigned_values) == 3
    assert assigned_values[0]["slug"] == expected_first_product.slug
    assert assigned_values[1]["slug"] == expected_second_product.slug
    assert assigned_values[2]["slug"] == expected_third_product.slug

    variant.refresh_from_db()
    assert list(
        variant.attributes.first().variantvalueassignment.values_list(
            "value_id", flat=True
        )
    ) == [attr_value_2.pk, attr_value_1.pk, attr_value_3.pk]


@pytest.mark.parametrize(
    ("values", "message", "code"),
    [
        (
            ["one", "two"],
            "Attribute must take only one value.",
            "INVALID",
        ),
        (["   "], "Attribute values cannot be blank.", "REQUIRED"),
    ],
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
    assert len(content["data"]["productVariantUpdate"]["errors"]) == 1, (
        f"expected: {message}"
    )
    errors = content["data"]["productVariantUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "attributes"
    assert errors[0]["code"] == code
    assert errors[0]["message"] == message
    assert set(errors[0]["attributes"]) == {attr_id}
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
    errors = content["data"]["productVariantUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "attributes"
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
    assert errors[0]["message"] == "Attribute expects a value but none were given."
    assert set(errors[0]["attributes"]) == {attr_id}
    assert not variant.product.variants.filter(sku=sku).exists()


def test_update_product_variant_with_reference_attributes_ref_not_in_available_choices(
    staff_api_client,
    product_list,
    page,
    product_type_page_reference_attribute,
    product_type_product_reference_attribute,
    product_type_variant_reference_attribute,
    permission_manage_products,
    page_type_list,
    product_type_with_variant_attributes,
):
    # given
    variant = product_list[0].variants.first()
    sku = str(uuid4())[:12]
    assert not variant.sku == sku

    product_type = variant.product.product_type
    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(
        product_type_page_reference_attribute,
        product_type_product_reference_attribute,
        product_type_variant_reference_attribute,
    )

    reference_product = product_list[1]
    reference_variant = product_list[2].variants.first()
    # assigned reference types that do not match product/page types of references
    # that are provided in the input
    product_type_page_reference_attribute.reference_page_types.add(page_type_list[1])
    product_type_product_reference_attribute.reference_product_types.add(
        product_type_with_variant_attributes
    )
    product_type_variant_reference_attribute.reference_product_types.add(
        product_type_with_variant_attributes
    )

    page_ref_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.id
    )
    product_ref_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.id
    )
    variant_ref_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_variant_reference_attribute.id
    )
    variant_ref = graphene.Node.to_global_id("ProductVariant", reference_variant.pk)
    page_ref = graphene.Node.to_global_id("Page", page.pk)
    product_ref = graphene.Node.to_global_id("Product", reference_product.pk)

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": page_ref_attr_id, "references": [page_ref]},
            {"id": product_ref_attr_id, "references": [product_ref]},
            {"id": variant_ref_attr_id, "references": [variant_ref]},
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
    errors = data["errors"]
    assert not data["productVariant"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.INVALID.name
    assert errors[0]["field"] == "attributes"
    assert set(errors[0]["attributes"]) == {
        page_ref_attr_id,
        product_ref_attr_id,
        variant_ref_attr_id,
    }


def test_update_product_variant_attribute_by_external_reference_value_created(
    staff_api_client,
    variant,
    product_type,
    permission_manage_products,
):
    # given
    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    attribute = product_type.variant_attributes.first()
    attr_external_ref = "test-attribute-ext-ref"
    attribute.external_reference = attr_external_ref
    attribute.save(update_fields=["external_reference"])

    values_count = attribute.values.count()
    value_external_ref = "test-value-ext-ref"
    value = "test-value"

    variables = {
        "id": variant_id,
        "attributes": [
            {
                "externalReference": attr_external_ref,
                "dropdown": {"externalReference": value_external_ref, "value": value},
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)["data"]["productVariantUpdate"]
    assert not content["errors"]
    data = content["productVariant"]
    assert len(data["attributes"]) == 1
    assert data["attributes"][0]["attribute"]["slug"] == attribute.slug
    assert data["attributes"][0]["values"][0]["slug"] == value
    attribute.refresh_from_db()
    assert attribute.values.count() == values_count + 1


def test_update_product_variant_attribute_by_external_reference_existing_value(
    staff_api_client,
    variant,
    product_type,
    permission_manage_products,
):
    # given
    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    attribute = product_type.variant_attributes.first()
    attr_external_ref = "test-attribute-ext-ref"
    attribute.external_reference = attr_external_ref
    attribute.save(update_fields=["external_reference"])

    value_external_ref = "test-value-ext-ref"
    value = attribute.values.create(
        name="Big", slug="big", external_reference=value_external_ref
    )
    values_count = attribute.values.count()

    variables = {
        "id": variant_id,
        "attributes": [
            {
                "externalReference": attr_external_ref,
                "dropdown": {
                    "externalReference": value_external_ref,
                    "value": value.name,
                },
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)["data"]["productVariantUpdate"]
    assert not content["errors"]
    data = content["productVariant"]
    assert len(data["attributes"]) == 1
    assert data["attributes"][0]["attribute"]["slug"] == attribute.slug
    assert data["attributes"][0]["values"][0]["name"] == value.name
    attribute.refresh_from_db()
    assert attribute.values.count() == values_count


def test_update_product_variant_attribute_by_external_reference_invalid_value(
    staff_api_client,
    variant,
    product_type,
    permission_manage_products,
):
    # given attributes input with external ref but value that does not match
    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    attribute = product_type.variant_attributes.first()
    attr_external_ref = "test-attribute-ext-ref"
    attribute.external_reference = attr_external_ref
    attribute.save(update_fields=["external_reference"])

    value = attribute.values.first()
    value_external_ref = "test-value-ext-ref"
    value.external_reference = value_external_ref
    value.save(update_fields=["external_reference"])
    attr_value = "test-value"

    variables = {
        "id": variant_id,
        "attributes": [
            {
                "externalReference": attr_external_ref,
                "dropdown": {
                    "externalReference": value_external_ref,
                    "value": attr_value,
                },
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)["data"]["productVariantUpdate"]
    assert len(content["errors"]) == 1
    assert not content["productVariant"]
    assert content["errors"][0]["field"] == "attributes"
    assert content["errors"][0]["code"] == "INVALID"


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
        (datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=3))
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
    data = content["data"]["productVariantUpdate"]["productVariant"]

    assert data["sku"] == sku
    assert data["preorder"]["globalThreshold"] == new_global_threshold
    assert data["preorder"]["endDate"] == new_preorder_end_date


def test_update_product_variant_can_not_turn_off_preorder(
    staff_api_client,
    permission_manage_products,
    preorder_variant_global_threshold,
):
    """Test that preorder cannot be disabled through updating the `preorder` field directly."""
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
    data = content["data"]["productVariantUpdate"]["productVariant"]

    assert data["sku"] == sku
    assert data["preorder"]["globalThreshold"] == variant.preorder_global_threshold
    assert data["preorder"]["endDate"] is None


# Query used to check how Product Variant metadata updates behaves
# and which events are emitted
UPDATE_METADATA_QUERY = """
        mutation updateVariant (
            $id: ID!,
            $input: ProductVariantInput!
            ) {
                productVariantUpdate(
                     id: $id,
                     input: $input
                    ) {
                    productVariant {
                        id
                        name
                    }
                    errors {
                        field
                        code
                    }
                }
            }
    """


@pytest.mark.parametrize(
    ("model_field", "metadata_field"),
    [
        ("metadata", "metadata"),
        ("private_metadata", "privateMetadata"),
    ],
)
@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_metadata_updated")
def test_update_product_variant_metadata_changed_legacy_webhook_on(
    product_variant_metadata_updated_mock,
    product_variant_updated_mock,
    staff_api_client,
    product,
    permission_manage_products,
    site_settings,
    model_field,
    metadata_field,
):
    # Given
    site_settings.use_legacy_update_webhook_emission = True
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])

    variant = product.variants.first()
    variant.name = "Name"
    variant.save(update_fields=["name"])
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    metadata_key = "key"
    metadata_value = "value"

    variables = {
        "id": variant_id,
        "input": {
            metadata_field: [{"key": metadata_key, "value": metadata_value}],
        },
    }

    # When
    response = staff_api_client.post_graphql(
        UPDATE_METADATA_QUERY, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]

    # Then
    assert not data["errors"]
    assert getattr(variant, model_field)[metadata_key] == metadata_value
    product_variant_updated_mock.assert_called_once_with(variant)
    product_variant_metadata_updated_mock.assert_called_once_with(variant)


@pytest.mark.parametrize(
    ("model_field", "metadata_field"),
    [
        ("metadata", "metadata"),
        ("private_metadata", "privateMetadata"),
    ],
)
@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_metadata_updated")
def test_update_product_variant_metadata_changed_legacy_webhook_off(
    product_variant_metadata_updated_mock,
    product_variant_updated_mock,
    staff_api_client,
    product,
    permission_manage_products,
    site_settings,
    model_field,
    metadata_field,
):
    # Given
    site_settings.use_legacy_update_webhook_emission = False
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])

    variant = product.variants.first()
    variant.name = "Name"
    variant.save(update_fields=["name"])
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    metadata_key = "key"
    metadata_value = "value"

    variables = {
        "id": variant_id,
        "input": {
            metadata_field: [{"key": metadata_key, "value": metadata_value}],
        },
    }

    # When
    response = staff_api_client.post_graphql(
        UPDATE_METADATA_QUERY, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]

    # Then
    assert not data["errors"]
    assert getattr(variant, model_field)[metadata_key] == metadata_value
    product_variant_updated_mock.assert_not_called()
    product_variant_metadata_updated_mock.assert_called_once_with(variant)


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_metadata_updated")
def test_update_product_variant_with_no_metadata_and_no_event(
    product_variant_metadata_updated_webhook_mock,
    product_variant_updated_webhook_mock,
    staff_api_client,
    product,
    permission_manage_products,
):
    # Given
    # - Metadata in variant is empty
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    assert variant.metadata == {}
    assert variant.private_metadata == {}

    # When
    # - Variant attribute is being updated
    # - Metadata is NOT being updated
    new_name = "New Name"
    variables = {"id": variant_id, "input": {"name": new_name}}

    response = staff_api_client.post_graphql(
        UPDATE_METADATA_QUERY, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]["productVariant"]

    assert data["id"] == variant_id
    assert data["name"] == new_name

    # Then
    # - product_variant_updated should run - field changed
    # - product_variant_metadata_updated should not run - metadata not changed,
    # no empty event emitted
    product_variant_updated_webhook_mock.assert_called_once_with(
        product.variants.last()
    )
    product_variant_metadata_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_metadata_updated")
def test_update_product_variant_with_existing_metadata_and_no_event(
    product_variant_metadata_updated_webhook_mock,
    product_variant_updated_webhook_mock,
    staff_api_client,
    product,
    permission_manage_products,
):
    # Given
    # - Metadata in variant is already existing
    # - mutation doesn't provide metadata

    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variant.name = "Name"
    variant.metadata = {
        "Foo": "Bar",
    }
    variant.private_metadata = {
        "Foo": "Bar",
    }
    variant.save(update_fields=["name", "metadata", "private_metadata"])

    # When
    # - Variant attribute is being updated
    # - Metadata is NOT being updated
    new_name = "New Name"
    variables = {"id": variant_id, "input": {"name": new_name}}

    response = staff_api_client.post_graphql(
        UPDATE_METADATA_QUERY, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]["productVariant"]

    assert data["id"] == variant_id
    assert data["name"] == new_name

    # Then
    # - product_variant_updated should run - field changed
    # - product_variant_metadata_updated should not run - metadata not changed,
    # no empty event emitted
    product_variant_updated_webhook_mock.assert_called_once_with(
        product.variants.last()
    )
    product_variant_metadata_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_metadata_updated")
def test_update_product_variant_with_existing_metadata_and_no_event_when_write_the_same(
    product_variant_metadata_updated_webhook_mock,
    product_variant_updated_webhook_mock,
    staff_api_client,
    product,
    permission_manage_products,
):
    # Given
    # - Metadata in variant is already existing
    # - mutation writes the same metadata key and value

    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    metadata_key = "mk"
    metadata_value = "mv"

    variant.name = "Name"
    variant.metadata = {metadata_key: metadata_value}
    variant.private_metadata = {metadata_key: metadata_value}
    variant.save(update_fields=["name", "metadata", "private_metadata"])

    assert variant.metadata == {metadata_key: metadata_value}

    assert variant.private_metadata == {metadata_key: metadata_value}

    # When
    # - Metadata is updated with the same values
    variables = {
        "id": variant_id,
        "input": {
            "metadata": [{"key": metadata_key, "value": metadata_value}],
            "privateMetadata": [{"key": metadata_key, "value": metadata_value}],
        },
    }

    response = staff_api_client.post_graphql(
        UPDATE_METADATA_QUERY, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]["productVariant"]

    assert data["id"] == variant_id

    # Then
    # - product_variant_updated should not run - nothing changed
    # - product_variant_metadata_updated should not run - metadata not changed, values the same,
    # no empty event emitted
    product_variant_updated_webhook_mock.assert_not_called()
    product_variant_metadata_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_metadata_updated")
def test_update_product_variant_with_existing_metadata_and_event_when_write_different_value(
    product_variant_metadata_updated_webhook_mock,
    product_variant_updated_webhook_mock,
    staff_api_client,
    product,
    permission_manage_products,
    site_settings,
):
    # Given
    # - Metadata in variant is already existing
    # - mutation writes the same metadata key but different value
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    metadata_key = "mk"
    metadata_value = "mv"

    variant.name = "Name"
    variant.metadata = {metadata_key: metadata_value}
    variant.private_metadata = {metadata_key: metadata_value}
    variant.save()

    site_settings.use_legacy_update_webhook_emission = False
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])

    # When
    # - Metadata is updated with the same values
    variables = {
        "id": variant_id,
        "input": {
            "metadata": [{"key": metadata_key, "value": "new value"}],
            "privateMetadata": [{"key": metadata_key, "value": "new value"}],
        },
    }

    response = staff_api_client.post_graphql(
        UPDATE_METADATA_QUERY, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]["productVariant"]

    assert data["id"] == variant_id

    # Then
    # - product_variant_updated should not run - only metadata value changed
    # - product_variant_metadata_updated should  run - metadata value changed
    # no empty event emitted
    product_variant_updated_webhook_mock.assert_not_called()
    product_variant_metadata_updated_webhook_mock.assert_called_once()


PRODUCT_VARIANT_UPDATE_MUTATION = """
mutation ProductVariantUpdate($id: ID!, $input: ProductVariantInput!) {
  productVariantUpdate(id: $id, input: $input) {
    errors {
      field
      code
      message
    }
    productVariant {
      id
    }
  }
}
"""


@patch(
    "saleor.graphql.product.mutations.product_variant.ProductVariantUpdate.call_event"
)
@patch(
    "saleor.graphql.product.mutations.product_variant.ProductVariantUpdate._save_variant_instance"
)
def test_update_product_variant_nothing_changed(
    save_variant_mock,
    call_event_mock,
    staff_api_client,
    product_with_variant_with_two_attributes,
    permission_manage_products,
    color_attribute,
    size_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    product = product_with_variant_with_two_attributes
    variant = product.variants.first()

    variant.name = "some_name"
    variant.sku = "some_sku"
    variant.external_reference = "some-ext-ref"
    key = "some_key"
    value = "some_value"
    variant.metadata = {key: value}
    variant.private_metadata = {key: value}
    variant.is_preorder = True
    variant.preorder_global_threshold = 10
    variant.preorder_end_date = "2024-12-02T00:00Z"
    variant.track_inventory = True
    variant.weight = Weight(kg=10)
    variant.quantity_limit_per_customer = 10
    variant.save()

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)

    attribute_slug_1 = variant.attributes.first().values.first().slug
    attribute_slug_2 = variant.attributes.last().values.first().slug

    input_fields = [
        snake_to_camel_case(key) for key in ProductVariantInput._meta.fields.keys()
    ]

    input = {
        "attributes": [
            {"id": color_attribute_id, "values": [attribute_slug_1]},
            {"id": size_attribute_id, "values": [attribute_slug_2]},
        ],
        "sku": variant.sku,
        "name": variant.name,
        "trackInventory": variant.track_inventory,
        "weight": 10,
        "preorder": {
            "globalThreshold": variant.preorder_global_threshold,
            "endDate": variant.preorder_end_date,
        },
        "quantityLimitPerCustomer": variant.quantity_limit_per_customer,
        "metadata": [{"key": key, "value": value}],
        "privateMetadata": [{"key": key, "value": value}],
        "externalReference": variant.external_reference,
    }
    assert set(input_fields) == set(input.keys())

    variables = {"id": variant_id, "input": input}

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_UPDATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["productVariantUpdate"]["errors"]
    variant.refresh_from_db()
    call_event_mock.assert_not_called()
    save_variant_mock.assert_not_called()


@patch(
    "saleor.graphql.product.mutations.product_variant.ProductVariantUpdate.call_event"
)
@patch(
    "saleor.graphql.product.mutations.product_variant.ProductVariantUpdate._save_variant_instance"
)
def test_update_product_variant_emit_event(
    save_variant_mock,
    call_event_mock,
    staff_api_client,
    product_with_variant_with_two_attributes,
    permission_manage_products,
    color_attribute,
    size_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    product = product_with_variant_with_two_attributes
    variant = product.variants.first()

    variant.name = "some_name"
    variant.sku = "some_sku"
    variant.external_reference = "some-ext-ref"
    key = "some_key"
    value = "some_value"
    variant.metadata = {key: value}
    variant.private_metadata = {key: value}
    variant.is_preorder = True
    variant.preorder_global_threshold = 10
    variant.preorder_end_date = "2024-12-02T00:00Z"
    variant.track_inventory = True
    variant.weight = Weight(kg=10)
    variant.quantity_limit_per_customer = 10
    variant.save()

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)

    input_fields = [
        snake_to_camel_case(key) for key in ProductVariantInput._meta.fields.keys()
    ]

    input = {
        "attributes": [
            {"id": color_attribute_id, "values": ["new_color"]},
            {"id": size_attribute_id, "values": ["new_size"]},
        ],
        "sku": variant.sku + "_new",
        "name": variant.name + "_new",
        "trackInventory": not variant.track_inventory,
        "weight": 11,
        "preorder": {
            "globalThreshold": variant.preorder_global_threshold + 1,
            "endDate": "2024-12-03T00:00Z",
        },
        "quantityLimitPerCustomer": variant.quantity_limit_per_customer + 1,
        "metadata": [{"key": key + "_new", "value": value + "_new"}],
        "privateMetadata": [{"key": key + "_new", "value": value + "_new"}],
        "externalReference": variant.external_reference + "_new",
    }
    assert set(input_fields) == set(input.keys())

    # fields making changes to related models (other than variant)
    non_variant_instance_fields = ["attributes"]

    for key, value in input.items():
        variables = {"id": variant_id, "input": {key: value}}

        # when
        response = staff_api_client.post_graphql(
            PRODUCT_VARIANT_UPDATE_MUTATION,
            variables,
        )
        content = get_graphql_content(response)

        # then
        assert not content["data"]["productVariantUpdate"]["errors"]
        call_event_mock.assert_called()
        call_event_mock.reset_mock()
        if key not in non_variant_instance_fields:
            save_variant_mock.assert_called()
            save_variant_mock.reset_mock()


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_metadata_updated")
def test_update_product_variant_sku_and_name_changed(
    product_variant_metadata_updated_mock,
    product_variant_updated_mock,
    staff_api_client,
    product,
    permission_manage_products,
):
    # Given
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    new_sku = "new-sku"
    new_name = "new-name"

    variables = {
        "id": variant_id,
        "input": {
            "sku": new_sku,
            "name": new_name,
        },
    }

    # When
    response = staff_api_client.post_graphql(
        UPDATE_METADATA_QUERY, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]

    # Then
    assert not data["errors"]
    assert variant.sku == new_sku
    assert variant.name == new_name
    product_variant_updated_mock.assert_called_once_with(variant)
    product_variant_metadata_updated_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_metadata_updated")
def test_update_product_variant_data_and_metadata_changed_legacy_webhook_off(
    product_variant_metadata_updated_mock,
    product_variant_updated_mock,
    staff_api_client,
    product,
    permission_manage_products,
    site_settings,
):
    # Given
    site_settings.use_legacy_update_webhook_emission = False
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])

    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    new_sku = "new-sku"
    metadata_key = "key"
    metadata_value = "value"

    variables = {
        "id": variant_id,
        "input": {
            "sku": new_sku,
            "metadata": [{"key": metadata_key, "value": metadata_value}],
            "privateMetadata": [{"key": metadata_key, "value": metadata_value}],
        },
    }

    # When
    response = staff_api_client.post_graphql(
        UPDATE_METADATA_QUERY, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]

    # Then
    assert not data["errors"]
    assert variant.sku == new_sku
    product_variant_updated_mock.assert_called_once_with(variant)
    product_variant_metadata_updated_mock.assert_called_once_with(variant)
