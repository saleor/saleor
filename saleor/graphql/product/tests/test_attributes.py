from unittest import mock

import graphene
import pytest

from ....attribute import AttributeInputType, AttributeType
from ....attribute.models import (
    AssignedProductAttributeValue,
    Attribute,
    AttributeProduct,
    AttributeValue,
    AttributeVariant,
)
from ....attribute.tests.model_helpers import (
    get_product_attribute_values,
    get_product_attributes,
)
from ....attribute.utils import associate_attribute_values_to_instance
from ....product import ProductTypeKind
from ....product.error_codes import ProductErrorCode
from ....product.models import Product, ProductType
from ...attribute.enums import AttributeTypeEnum
from ...core.utils import snake_to_camel_case
from ...tests.utils import get_graphql_content
from ..enums import ProductAttributeType

QUERY_PRODUCT_AND_VARIANTS_ATTRIBUTES = """
    query ($channel: String){
      products(first: 1, channel: $channel) {
        edges {
          node {
            attributes {
              attribute {
                slug
                type
              }
              values {
                slug
              }
            }
            variants {
              attributes {
                attribute {
                  slug
                  type
                }
                values {
                  slug
                }
              }
            }
          }
        }
      }
    }
"""


@pytest.mark.parametrize("is_staff", [False, True])
def test_resolve_attributes_with_hidden(
    user_api_client,
    staff_api_client,
    product,
    color_attribute,
    size_attribute,
    is_staff,
    permission_manage_products,
    channel_USD,
):
    """Test that only staff users can see hidden attributes."""
    variables = {"channel": channel_USD.slug}
    query = QUERY_PRODUCT_AND_VARIANTS_ATTRIBUTES
    api_client = user_api_client

    variant = product.variants.first()

    product_attribute = color_attribute
    variant_attribute = size_attribute

    expected_product_attribute_count = get_product_attributes(product).count() - 1
    expected_variant_attribute_count = variant.attributes.count() - 1

    if is_staff:
        api_client = staff_api_client
        api_client.user.user_permissions.add(permission_manage_products)
        expected_product_attribute_count += 1
        expected_variant_attribute_count += 1

    # Hide one product and variant attribute from the storefront
    for attribute in (product_attribute, variant_attribute):
        attribute.visible_in_storefront = False
        attribute.save(update_fields=["visible_in_storefront"])

    product = get_graphql_content(api_client.post_graphql(query, variables))["data"][
        "products"
    ]["edges"][0]["node"]

    assert len(product["attributes"]) == expected_product_attribute_count
    assert len(product["variants"][0]["attributes"]) == expected_variant_attribute_count


def test_resolve_attribute_values(user_api_client, product, staff_user, channel_USD):
    """Ensure the attribute values are properly resolved."""
    variables = {"channel": channel_USD.slug}
    query = QUERY_PRODUCT_AND_VARIANTS_ATTRIBUTES
    api_client = user_api_client

    variant = product.variants.first()

    assert get_product_attributes(product).count() == 1
    assert variant.attributes.count() == 1

    attribute = get_product_attributes(product).first()
    product_attribute_values = list(
        get_product_attribute_values(product, attribute).values_list("slug", flat=True)
    )
    variant_attribute_values = list(
        variant.attributes.first().values.values_list("slug", flat=True)
    )

    assert len(product_attribute_values) == 1
    assert len(variant_attribute_values) == 1

    product = get_graphql_content(api_client.post_graphql(query, variables))["data"][
        "products"
    ]["edges"][0]["node"]

    product_attributes = product["attributes"]
    variant_attributes = product["variants"][0]["attributes"]

    assert len(product_attributes) == len(product_attribute_values)
    assert len(variant_attributes) == len(variant_attribute_values)

    assert product_attributes[0]["attribute"]["slug"] == "color"
    assert (
        product_attributes[0]["attribute"]["type"]
        == AttributeTypeEnum.PRODUCT_TYPE.name
    )
    assert product_attributes[0]["values"][0]["slug"] == product_attribute_values[0]

    assert variant_attributes[0]["attribute"]["slug"] == "size"
    assert (
        variant_attributes[0]["attribute"]["type"]
        == AttributeTypeEnum.PRODUCT_TYPE.name
    )


def test_resolve_attribute_values_non_assigned_to_node(
    user_api_client, product, staff_user, channel_USD
):
    """Test that excessive attributes are not listed even if present."""
    variables = {"channel": channel_USD.slug}
    query = QUERY_PRODUCT_AND_VARIANTS_ATTRIBUTES
    api_client = user_api_client

    variant = product.variants.first()
    product_type = product.product_type

    # Create dummy attributes
    unassigned_product_attribute = Attribute.objects.create(
        name="P", slug="product", type=AttributeType.PRODUCT_TYPE
    )
    unassigned_variant_attribute = Attribute.objects.create(
        name="V", slug="variant", type=AttributeType.PRODUCT_TYPE
    )

    # Create a value for each dummy attribute to ensure they are not returned
    # by the product or variant as they are not associated to them
    AttributeValue.objects.bulk_create(
        [
            AttributeValue(slug="a", name="A", attribute=unassigned_product_attribute),
            AttributeValue(slug="b", name="B", attribute=unassigned_product_attribute),
        ]
    )

    # Assign the dummy attributes to the product type and push them at the top
    # through a sort_order=0 as the other attributes have sort_order=null
    AttributeProduct.objects.create(
        attribute=unassigned_product_attribute, product_type=product_type, sort_order=0
    )
    AttributeVariant.objects.create(
        attribute=unassigned_variant_attribute,
        product_type=product_type,
        sort_order=0,
    )

    # All attributes assigned for the same product type should be returned
    assert get_product_attributes(product).count() == 2

    # no additional values should be added
    assert product.attributevalues.count() == 1
    assert variant.attributes.count() == 1

    product = get_graphql_content(api_client.post_graphql(query, variables))["data"][
        "products"
    ]["edges"][0]["node"]

    product_attributes = product["attributes"]
    variant_attributes = product["variants"][0]["attributes"]

    assert len(product_attributes) == 2, "Non-assigned attr from the PT may be missing"
    assert len(variant_attributes) == 2, "Non-assigned attr from the PT may be missing"

    assert product_attributes[0]["attribute"]["slug"] == "product"
    assert product_attributes[0]["values"] == []

    assert variant_attributes[0]["attribute"]["slug"] == "variant"
    assert variant_attributes[0]["values"] == []


def test_resolve_assigned_attribute_without_values(
    api_client, product_type, product, channel_USD
):
    """Test that all attributes are listed even if values are missing."""
    # Retrieve the product's variant
    variant = product.variants.get()

    # Remove all attributes and values from the product and its variant
    AssignedProductAttributeValue.objects.filter(product_id=product.pk).delete()
    variant.attributesrelated.clear()

    # Retrieve the product and variant's attributes
    products = get_graphql_content(
        api_client.post_graphql(
            """
        query ($channel: String) {
          products(first: 10, channel: $channel) {
            edges {
              node {
                attributes {
                  attribute {
                    slug
                  }
                  values {
                    name
                  }
                }
                variants {
                  attributes {
                    attribute {
                      slug
                    }
                    values {
                      name
                    }
                  }
                }
              }
            }
          }
        }
    """,
            {"channel": channel_USD.slug},
        )
    )["data"]["products"]["edges"]

    # Ensure we are only working on one product and variant, the ones we are testing
    assert len(products) == 1
    assert len(products[0]["node"]["variants"]) == 1

    # Retrieve the nodes data
    product = products[0]["node"]
    variant = product["variants"][0]

    # Ensure the product attributes values are all None
    assert len(product["attributes"]) == 1
    assert product["attributes"][0]["attribute"]["slug"] == "color"
    assert product["attributes"][0]["values"] == []

    # Ensure the variant attributes values are all None
    assert variant["attributes"][0]["attribute"]["slug"] == "size"
    assert variant["attributes"][0]["values"] == []


PRODUCT_ASSIGN_ATTR_QUERY = """
    mutation assign($productTypeId: ID!, $operations: [ProductAttributeAssignInput!]!) {
      productAttributeAssign(productTypeId: $productTypeId, operations: $operations) {
        errors {
          field
          code
          message
          attributes
        }
        productType {
          id
          productAttributes {
            id
            visibleInStorefront
            filterableInDashboard
            filterableInStorefront
          }
          variantAttributes {
            id
            visibleInStorefront
            filterableInDashboard
            filterableInStorefront
            availableInGrid
            valueRequired
            storefrontSearchPosition
          }
        }
      }
    }
"""


def test_assign_attributes_to_product_type(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    product_type_attribute_list,
):
    product_type = ProductType.objects.create(
        name="Default Type",
        has_variants=True,
        kind=ProductTypeKind.NORMAL,
    )
    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    query = PRODUCT_ASSIGN_ATTR_QUERY
    operations = []
    variables = {"productTypeId": product_type_global_id, "operations": operations}

    product_attributes_ids = {attr.pk for attr in product_type_attribute_list[:2]}
    variant_attributes_ids = {attr.pk for attr in product_type_attribute_list[2:]}

    for attr_id in product_attributes_ids:
        operations.append(
            {"type": "PRODUCT", "id": graphene.Node.to_global_id("Attribute", attr_id)}
        )

    for attr_id in variant_attributes_ids:
        operations.append(
            {"type": "VARIANT", "id": graphene.Node.to_global_id("Attribute", attr_id)}
        )

    content = get_graphql_content(
        staff_api_client.post_graphql(
            query,
            variables,
            permissions=[permission_manage_product_types_and_attributes],
        )
    )["data"]["productAttributeAssign"]
    assert not content["errors"], "Should have succeeded"

    assert content["productType"]["id"] == product_type_global_id
    assert len(content["productType"]["productAttributes"]) == len(
        product_attributes_ids
    )
    assert len(content["productType"]["variantAttributes"]) == len(
        variant_attributes_ids
    )

    found_product_attrs_ids = {
        int(graphene.Node.from_global_id(attr["id"])[1])
        for attr in content["productType"]["productAttributes"]
    }
    found_variant_attrs_ids = {
        int(graphene.Node.from_global_id(attr["id"])[1])
        for attr in content["productType"]["variantAttributes"]
    }

    assert found_product_attrs_ids == product_attributes_ids
    assert found_variant_attrs_ids == variant_attributes_ids


def test_assign_non_existing_attributes_to_product_type(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    product_type_attribute_list,
):
    product_type = ProductType.objects.create(
        name="Default Type", has_variants=True, kind=ProductTypeKind.NORMAL
    )
    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    query = PRODUCT_ASSIGN_ATTR_QUERY
    attribute_id = graphene.Node.to_global_id("Attribute", "55511155593")
    operations = [{"type": "PRODUCT", "id": attribute_id}]
    variables = {"productTypeId": product_type_global_id, "operations": operations}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    content = content["data"]["productAttributeAssign"]
    assert content["errors"][0]["code"] == ProductErrorCode.NOT_FOUND.name
    assert content["errors"][0]["field"] == "operations"
    assert content["errors"][0]["attributes"] == [attribute_id]


def test_assign_variant_attribute_to_product_type_with_disabled_variants(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    product_type_without_variant,
    color_attribute_without_values,
):
    product_type = product_type_without_variant
    attribute = color_attribute_without_values
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )

    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    query = PRODUCT_ASSIGN_ATTR_QUERY
    operations = [
        {"type": "VARIANT", "id": graphene.Node.to_global_id("Attribute", attribute.pk)}
    ]
    variables = {"productTypeId": product_type_global_id, "operations": operations}

    content = get_graphql_content(staff_api_client.post_graphql(query, variables))[
        "data"
    ]["productAttributeAssign"]
    assert content["errors"][0]["field"] == "operations"
    assert (
        content["errors"][0]["message"] == "Variants are disabled in this product type."
    )
    assert (
        content["errors"][0]["code"]
        == ProductErrorCode.ATTRIBUTE_VARIANTS_DISABLED.name
    )


def test_assign_variant_attribute_having_multiselect_input_type(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    product_type,
    size_attribute,
):
    attribute = size_attribute
    attribute.input_type = AttributeInputType.MULTISELECT
    attribute.save(update_fields=["input_type"])
    product_type.variant_attributes.clear()

    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )

    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    attr_id = graphene.Node.to_global_id("Attribute", attribute.pk)

    query = PRODUCT_ASSIGN_ATTR_QUERY
    operations = [{"type": "VARIANT", "id": attr_id}]
    variables = {"productTypeId": product_type_global_id, "operations": operations}

    content = get_graphql_content(staff_api_client.post_graphql(query, variables))[
        "data"
    ]["productAttributeAssign"]
    assert not content["errors"]
    assert content["productType"]["id"] == product_type_global_id
    assert len(content["productType"]["variantAttributes"]) == 1
    assert content["productType"]["variantAttributes"][0]["id"] == attr_id


def test_assign_variant_attribute_having_multiselect_input_type_with_variant_selection(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    product_type,
    size_attribute,
):
    attribute = size_attribute
    attribute.input_type = AttributeInputType.MULTISELECT
    attribute.save(update_fields=["input_type"])
    product_type.variant_attributes.clear()

    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )

    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    attr_id = graphene.Node.to_global_id("Attribute", attribute.pk)

    query = PRODUCT_ASSIGN_ATTR_QUERY
    operations = [{"type": "VARIANT", "id": attr_id, "variantSelection": True}]
    variables = {"productTypeId": product_type_global_id, "operations": operations}

    content = get_graphql_content(staff_api_client.post_graphql(query, variables))[
        "data"
    ]["productAttributeAssign"]

    assert content["errors"][0]["field"] == "operations"
    assert content["errors"][0]["message"] == (
        "Some of the attributes types are not supported for variant selection. "
        f"Supported types are: {AttributeInputType.ALLOWED_IN_VARIANT_SELECTION}."
    )
    assert (
        content["errors"][0]["code"]
        == ProductErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED.name
    )
    assert len(content["errors"]) == 1


def test_assign_product_attribute_having_variant_selection(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    product_type,
    size_attribute,
):
    attribute = size_attribute
    attribute.input_type = AttributeInputType.MULTISELECT
    attribute.save(update_fields=["input_type"])
    product_type.variant_attributes.clear()

    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )

    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    attr_id = graphene.Node.to_global_id("Attribute", attribute.pk)

    query = PRODUCT_ASSIGN_ATTR_QUERY
    operations = [{"type": "PRODUCT", "id": attr_id, "variantSelection": True}]
    variables = {"productTypeId": product_type_global_id, "operations": operations}

    content = get_graphql_content(staff_api_client.post_graphql(query, variables))[
        "data"
    ]["productAttributeAssign"]

    assert content["errors"][0]["field"] == "operations"
    assert (
        f"Attribute with pk: '{attribute.pk}' with different type than "
        f"'VARIANT' (found: 'PRODUCT') cannot be assigned with variant_selection: true."
    ) == content["errors"][0]["message"]
    assert (
        content["errors"][0]["code"]
        == ProductErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED.name
    )


@pytest.mark.parametrize(
    ("product_type_attribute_type", "gql_attribute_type"),
    [
        (ProductAttributeType.PRODUCT, ProductAttributeType.VARIANT),
        (ProductAttributeType.VARIANT, ProductAttributeType.PRODUCT),
        (ProductAttributeType.PRODUCT, ProductAttributeType.PRODUCT),
        (ProductAttributeType.VARIANT, ProductAttributeType.VARIANT),
    ],
)
def test_assign_attribute_to_product_type_having_already_that_attribute(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    color_attribute_without_values,
    product_type_attribute_type,
    gql_attribute_type,
):
    product_type = ProductType.objects.create(name="Type", kind=ProductTypeKind.NORMAL)
    attribute = color_attribute_without_values
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )

    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    if product_type_attribute_type == ProductAttributeType.PRODUCT:
        product_type.product_attributes.add(attribute)
    elif product_type_attribute_type == ProductAttributeType.VARIANT:
        product_type.variant_attributes.add(attribute)
    else:
        raise ValueError(f"Unknown: {product_type}")

    query = PRODUCT_ASSIGN_ATTR_QUERY
    operations = [
        {
            "type": gql_attribute_type.value,
            "id": graphene.Node.to_global_id("Attribute", attribute.pk),
        }
    ]
    variables = {"productTypeId": product_type_global_id, "operations": operations}

    content = get_graphql_content(staff_api_client.post_graphql(query, variables))[
        "data"
    ]["productAttributeAssign"]
    assert content["errors"][0]["field"] == "operations"
    assert (
        content["errors"][0]["message"]
        == "Color (color) have already been assigned to this product type."
    )
    assert (
        content["errors"][0]["code"] == ProductErrorCode.ATTRIBUTE_ALREADY_ASSIGNED.name
    )


PRODUCT_ASSIGN_ATTR_UPDATE_QUERY = """
    mutation assign(
      $productTypeId: ID!, $operations: [ProductAttributeAssignmentUpdateInput!]!
    ) {
      productAttributeAssignmentUpdate(
        productTypeId: $productTypeId, operations: $operations
      ) {
        errors {
          field
          code
          message
          attributes
        }
        productType {
          id
          productAttributes {
            id
          }
          variantAttributes {
            id
          }
        }
      }
    }
"""


def test_assignment_attribute_update_not_assigned_attribute_should_raise_an_error(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    color_attribute_without_values,
):
    product_type = ProductType.objects.create(name="Type", kind=ProductTypeKind.NORMAL)
    attribute = color_attribute_without_values
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )

    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    query = PRODUCT_ASSIGN_ATTR_UPDATE_QUERY
    operations = [
        {
            "id": graphene.Node.to_global_id("Attribute", attribute.pk),
            "variantSelection": True,
        }
    ]
    variables = {"productTypeId": product_type_global_id, "operations": operations}

    content = get_graphql_content(staff_api_client.post_graphql(query, variables))[
        "data"
    ]["productAttributeAssignmentUpdate"]

    expected_errors = [
        {
            "field": "operations",
            "message": "Attribute is not assigned to product type.",
            "code": ProductErrorCode.NOT_FOUND.name,
            "attributes": [graphene.Node.to_global_id("Attribute", attribute.pk)],
        },
        {
            "field": "operations",
            "message": "Attribute is not assigned to product variant.",
            "code": ProductErrorCode.NOT_FOUND.name,
            "attributes": [graphene.Node.to_global_id("Attribute", attribute.pk)],
        },
    ]
    assert len(content["errors"]) == 2

    for error in content["errors"]:
        assert error in expected_errors


def test_assignment_attribute_update_assigned_to_product_should_raise_an_error(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    color_attribute_without_values,
):
    product_type = ProductType.objects.create(name="Type", kind=ProductTypeKind.NORMAL)
    attribute = color_attribute_without_values
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )

    product_type.product_attributes.add(attribute)
    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    query = PRODUCT_ASSIGN_ATTR_UPDATE_QUERY
    operations = [
        {
            "id": graphene.Node.to_global_id("Attribute", attribute.pk),
            "variantSelection": True,
        }
    ]
    variables = {"productTypeId": product_type_global_id, "operations": operations}

    content = get_graphql_content(staff_api_client.post_graphql(query, variables))[
        "data"
    ]["productAttributeAssignmentUpdate"]

    expected_errors = [
        {
            "field": "operations",
            "message": "Attribute is not assigned to product variant.",
            "code": ProductErrorCode.NOT_FOUND.name,
            "attributes": [graphene.Node.to_global_id("Attribute", attribute.pk)],
        },
    ]
    assert len(content["errors"]) == 1

    for error in content["errors"]:
        assert error in expected_errors


def test_assignment_attrib_update_assigned_with_duplicates_type_should_raise_an_error(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    color_attribute_without_values,
):
    product_type = ProductType.objects.create(name="Type", kind=ProductTypeKind.NORMAL)
    attribute = color_attribute_without_values

    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )

    product_type.variant_attributes.add(attribute)
    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    query = PRODUCT_ASSIGN_ATTR_UPDATE_QUERY
    id_ = graphene.Node.to_global_id("Attribute", attribute.pk)
    operations = [
        {
            "id": id_,
            "variantSelection": True,
        },
        {
            "id": id_,
            "variantSelection": False,
        },
    ]
    variables = {"productTypeId": product_type_global_id, "operations": operations}

    content = get_graphql_content(staff_api_client.post_graphql(query, variables))[
        "data"
    ]["productAttributeAssignmentUpdate"]

    expected_error_msg = "Attribute ids should be unique within operations."

    expected_errors = [
        {
            "field": "operations",
            "message": expected_error_msg,
            "code": ProductErrorCode.INVALID.name,
            "attributes": [id_],
        },
    ]
    assert len(content["errors"]) == 1

    for error in content["errors"]:
        assert error in expected_errors


def test_assignment_attribute_update_assigned_unsupported_type_should_raise_an_error(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    color_attribute_without_values,
):
    product_type = ProductType.objects.create(name="Type", kind=ProductTypeKind.NORMAL)
    attribute = color_attribute_without_values
    attribute.input_type = AttributeInputType.MULTISELECT
    attribute.save(update_fields=["input_type"])

    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )

    product_type.variant_attributes.add(attribute)
    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    query = PRODUCT_ASSIGN_ATTR_UPDATE_QUERY
    operations = [
        {
            "id": graphene.Node.to_global_id("Attribute", attribute.pk),
            "variantSelection": True,
        }
    ]
    variables = {"productTypeId": product_type_global_id, "operations": operations}

    content = get_graphql_content(staff_api_client.post_graphql(query, variables))[
        "data"
    ]["productAttributeAssignmentUpdate"]

    expected_error_msg = (
        f"Some of the attributes types are not supported for "
        "variant selection. Supported types are: "
        f"{AttributeInputType.ALLOWED_IN_VARIANT_SELECTION}."
    )

    expected_errors = [
        {
            "field": "operations",
            "message": expected_error_msg,
            "code": ProductErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED.name,
            "attributes": [graphene.Node.to_global_id("Attribute", attribute.pk)],
        },
    ]
    assert len(content["errors"]) == 1

    for error in content["errors"]:
        assert error in expected_errors


def test_assignment_attribute_update_assigned_should_modify_variant_selection(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    size_attribute,
    color_attribute_without_values,
):
    product_type = ProductType.objects.create(name="Type", kind=ProductTypeKind.NORMAL)
    attribute_1 = color_attribute_without_values
    attribute_2 = size_attribute

    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )

    product_type.variant_attributes.add(
        attribute_1, through_defaults={"variant_selection": False}
    )
    product_type.variant_attributes.add(
        attribute_2, through_defaults={"variant_selection": True}
    )
    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    query = PRODUCT_ASSIGN_ATTR_UPDATE_QUERY
    operations = [
        {
            "id": graphene.Node.to_global_id("Attribute", attribute_1.pk),
            "variantSelection": True,
        },
        {
            "id": graphene.Node.to_global_id("Attribute", attribute_2.pk),
            "variantSelection": False,
        },
    ]
    variables = {"productTypeId": product_type_global_id, "operations": operations}

    content = get_graphql_content(staff_api_client.post_graphql(query, variables))[
        "data"
    ]["productAttributeAssignmentUpdate"]

    assert len(content["errors"]) == 0
    assert AttributeVariant.objects.get(attribute_id=attribute_1.pk).variant_selection
    assert not AttributeVariant.objects.get(
        attribute_id=attribute_2.pk
    ).variant_selection


def test_assignment_attrib_update_assigned_should_modify_variant_selection_from_ext_app(
    app_api_client,
    permission_manage_product_types_and_attributes,
    size_attribute,
    color_attribute_without_values,
):
    product_type = ProductType.objects.create(name="Type", kind=ProductTypeKind.NORMAL)
    attribute_1 = color_attribute_without_values
    attribute_2 = size_attribute

    app_api_client.app.permissions.add(permission_manage_product_types_and_attributes)

    product_type.variant_attributes.add(
        attribute_1, through_defaults={"variant_selection": False}
    )
    product_type.variant_attributes.add(
        attribute_2, through_defaults={"variant_selection": True}
    )
    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    query = PRODUCT_ASSIGN_ATTR_UPDATE_QUERY
    operations = [
        {
            "id": graphene.Node.to_global_id("Attribute", attribute_1.pk),
            "variantSelection": True,
        },
        {
            "id": graphene.Node.to_global_id("Attribute", attribute_2.pk),
            "variantSelection": False,
        },
    ]
    variables = {"productTypeId": product_type_global_id, "operations": operations}

    content = get_graphql_content(app_api_client.post_graphql(query, variables))[
        "data"
    ]["productAttributeAssignmentUpdate"]

    assert len(content["errors"]) == 0
    assert AttributeVariant.objects.get(attribute_id=attribute_1.pk).variant_selection
    assert not AttributeVariant.objects.get(
        attribute_id=attribute_2.pk
    ).variant_selection


def test_assign_page_attribute_to_product_type(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    tag_page_attribute,
    product_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )

    tag_page_attr_id = graphene.Node.to_global_id("Attribute", tag_page_attribute.pk)

    variables = {
        "productTypeId": graphene.Node.to_global_id("ProductType", product_type.pk),
        "operations": [
            {"type": ProductAttributeType.PRODUCT.value, "id": tag_page_attr_id},
        ],
    }

    # when
    response = staff_api_client.post_graphql(PRODUCT_ASSIGN_ATTR_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["productAttributeAssign"]
    errors = data["errors"]

    assert not data["productType"]
    assert len(errors) == 1
    assert errors[0]["field"] == "operations"
    assert errors[0]["code"] == ProductErrorCode.INVALID.name
    assert errors[0]["attributes"] == [tag_page_attr_id]


def test_assign_attribute_to_product_type_multiple_errors_returned(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    color_attribute,
    size_attribute,
    tag_page_attribute,
):
    # given
    product_type = ProductType.objects.create(name="Type", kind=ProductTypeKind.NORMAL)
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )

    product_type.product_attributes.add(color_attribute)

    unsupported_type_attr = size_attribute
    unsupported_type_attr.input_type = AttributeInputType.MULTISELECT
    unsupported_type_attr.save(update_fields=["input_type"])

    color_attr_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    unsupported_type_attr_id = graphene.Node.to_global_id(
        "Attribute", unsupported_type_attr.pk
    )
    tag_page_attr_id = graphene.Node.to_global_id("Attribute", tag_page_attribute.pk)

    variables = {
        "productTypeId": graphene.Node.to_global_id("ProductType", product_type.pk),
        "operations": [
            {"type": ProductAttributeType.PRODUCT.value, "id": color_attr_id},
            {
                "type": ProductAttributeType.VARIANT.value,
                "id": unsupported_type_attr_id,
            },
            {"type": ProductAttributeType.PRODUCT.value, "id": tag_page_attr_id},
        ],
    }

    # when
    response = staff_api_client.post_graphql(PRODUCT_ASSIGN_ATTR_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["productAttributeAssign"]
    errors = data["errors"]

    assert not data["productType"]
    assert len(errors) == 2
    expected_errors = [
        {
            "code": ProductErrorCode.ATTRIBUTE_ALREADY_ASSIGNED.name,
            "field": "operations",
            "message": mock.ANY,
            "attributes": [color_attr_id],
        },
        {
            "code": ProductErrorCode.INVALID.name,
            "field": "operations",
            "message": mock.ANY,
            "attributes": [tag_page_attr_id],
        },
    ]
    for error in expected_errors:
        assert error in errors


PRODUCT_UNASSIGN_ATTR_QUERY = """
    mutation ProductUnassignAttribute(
      $productTypeId: ID!, $attributeIds: [ID!]!
    ) {
      productAttributeUnassign(
          productTypeId: $productTypeId, attributeIds: $attributeIds
      ) {
        errors {
          field
          message
        }
        productType {
          id
          variantAttributes {
            id
          }
          productAttributes {
            id
          }
        }
      }
    }
"""


def test_unassign_attributes_from_product_type(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    product_type_attribute_list,
    category,
):
    product_type = ProductType.objects.create(name="Type", kind=ProductTypeKind.NORMAL)
    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    product = Product.objects.create(
        name="Test product",
        slug="test-product-11",
        product_type=product_type,
        category=category,
    )

    variant_attribute, *product_attributes = product_type_attribute_list
    product_type.product_attributes.add(*product_attributes)
    product_type.variant_attributes.add(variant_attribute)

    attribute = product_attributes[1]
    product_attr_value = AttributeValue.objects.create(
        attribute=attribute, name="Test value", slug="test-value"
    )
    associate_attribute_values_to_instance(
        product,
        {attribute.pk: [product_attr_value]},
    )

    remaining_attribute_global_id = graphene.Node.to_global_id(
        "Attribute", product_attributes[1].pk
    )

    query = PRODUCT_UNASSIGN_ATTR_QUERY
    variables = {
        "productTypeId": product_type_global_id,
        "attributeIds": [
            graphene.Node.to_global_id("Attribute", product_attributes[0].pk)
        ],
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(
            query,
            variables,
            permissions=[permission_manage_product_types_and_attributes],
        )
    )["data"]["productAttributeUnassign"]
    assert not content["errors"]

    assert content["productType"]["id"] == product_type_global_id
    assert len(content["productType"]["productAttributes"]) == 1
    assert len(content["productType"]["variantAttributes"]) == 1

    assert (
        content["productType"]["productAttributes"][0]["id"]
        == remaining_attribute_global_id
    )


def test_unassign_attributes_not_in_product_type(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    color_attribute_without_values,
):
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )

    product_type = ProductType.objects.create(name="Type", kind=ProductTypeKind.NORMAL)
    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    query = PRODUCT_UNASSIGN_ATTR_QUERY
    variables = {
        "productTypeId": product_type_global_id,
        "attributeIds": [
            graphene.Node.to_global_id("Attribute", color_attribute_without_values.pk)
        ],
    }

    content = get_graphql_content(staff_api_client.post_graphql(query, variables))[
        "data"
    ]["productAttributeUnassign"]
    assert not content["errors"]

    assert content["productType"]["id"] == product_type_global_id
    assert len(content["productType"]["productAttributes"]) == 0
    assert len(content["productType"]["variantAttributes"]) == 0


def test_retrieve_product_attributes_input_type(staff_api_client, product, channel_USD):
    query = """
        query ($channel: String){
          products(first: 10, channel: $channel) {
            edges {
              node {
                attributes {
                  values {
                    inputType
                  }
                }
              }
            }
          }
        }
    """

    variables = {"channel": channel_USD.slug}
    found_products = get_graphql_content(
        staff_api_client.post_graphql(query, variables)
    )["data"]["products"]["edges"]
    assert len(found_products) == 1

    for gql_attr in found_products[0]["node"]["attributes"]:
        assert len(gql_attr["values"]) == 1
        assert gql_attr["values"][0]["inputType"] == "DROPDOWN"


ATTRIBUTES_RESORT_QUERY = """
    mutation ProductTypeReorderAttributes(
      $productTypeId: ID!
      $moves: [ReorderInput!]!
      $type: ProductAttributeType!
    ) {
      productTypeReorderAttributes(
        productTypeId: $productTypeId
        moves: $moves
        type: $type
      ) {
        productType {
          id
          variantAttributes {
            id
            slug
          }
          productAttributes {
            id
          }
        }

        errors {
          field
          message
          code
          attributes
        }
      }
    }
"""


def test_sort_attributes_within_product_type_invalid_product_type(
    staff_api_client, permission_manage_product_types_and_attributes
):
    """Try to reorder an invalid product type (invalid ID)."""

    product_type_id = graphene.Node.to_global_id("ProductType", -1)
    attribute_id = graphene.Node.to_global_id("Attribute", -1)

    variables = {
        "type": "VARIANT",
        "productTypeId": product_type_id,
        "moves": [{"id": attribute_id, "sortOrder": 1}],
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(
            ATTRIBUTES_RESORT_QUERY,
            variables,
            permissions=[permission_manage_product_types_and_attributes],
        )
    )["data"]["productTypeReorderAttributes"]

    assert content["errors"] == [
        {
            "field": "productTypeId",
            "code": ProductErrorCode.NOT_FOUND.name,
            "message": f"Couldn't resolve to a product type: {product_type_id}",
            "attributes": None,
        }
    ]


def test_sort_attributes_within_product_type_invalid_id(
    staff_api_client, permission_manage_product_types_and_attributes, color_attribute
):
    """Try to reorder an attribute not associated to the given product type."""

    product_type = ProductType.objects.create(
        name="Dummy Type", kind=ProductTypeKind.NORMAL
    )
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)

    variables = {
        "type": "VARIANT",
        "productTypeId": product_type_id,
        "moves": [{"id": attribute_id, "sortOrder": 1}],
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(
            ATTRIBUTES_RESORT_QUERY,
            variables,
            permissions=[permission_manage_product_types_and_attributes],
        )
    )["data"]["productTypeReorderAttributes"]

    assert content["errors"] == [
        {
            "field": "moves",
            "message": "Couldn't resolve to an attribute.",
            "attributes": [attribute_id],
            "code": ProductErrorCode.NOT_FOUND.name,
        }
    ]


@pytest.mark.parametrize(
    ("attribute_type", "relation_field", "backref_field"),
    [
        ("VARIANT", "variant_attributes", "attributevariant"),
        ("PRODUCT", "product_attributes", "attributeproduct"),
    ],
)
def test_sort_attributes_within_product_type(
    staff_api_client,
    product_type_attribute_list,
    permission_manage_product_types_and_attributes,
    attribute_type,
    relation_field,
    backref_field,
):
    attributes = product_type_attribute_list
    assert len(attributes) == 3

    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )

    product_type = ProductType.objects.create(
        name="Dummy Type", kind=ProductTypeKind.NORMAL
    )
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)
    m2m_attributes = getattr(product_type, relation_field)
    m2m_attributes.set(attributes)

    sort_method = getattr(m2m_attributes, f"{relation_field}_sorted")
    attributes = list(sort_method())

    assert len(attributes) == 3

    variables = {
        "type": attribute_type,
        "productTypeId": product_type_id,
        "moves": [
            {
                "id": graphene.Node.to_global_id("Attribute", attributes[0].pk),
                "sortOrder": +1,
            },
            {
                "id": graphene.Node.to_global_id("Attribute", attributes[2].pk),
                "sortOrder": -1,
            },
        ],
    }

    expected_order = [attributes[1].pk, attributes[2].pk, attributes[0].pk]

    content = get_graphql_content(
        staff_api_client.post_graphql(ATTRIBUTES_RESORT_QUERY, variables)
    )["data"]["productTypeReorderAttributes"]
    assert not content["errors"]

    assert (
        content["productType"]["id"] == product_type_id
    ), "Did not return the correct product type"

    gql_attributes = content["productType"][snake_to_camel_case(relation_field)]
    assert len(gql_attributes) == len(expected_order)

    for attr, expected_pk in zip(gql_attributes, expected_order):
        gql_type, gql_attr_id = graphene.Node.from_global_id(attr["id"])
        assert gql_type == "Attribute"
        assert int(gql_attr_id) == expected_pk


PRODUCT_REORDER_ATTRIBUTE_VALUES_MUTATION = """
    mutation ProductReorderAttributeValues(
      $productId: ID!
      $attributeId: ID!
      $moves: [ReorderInput!]!
    ) {
      productReorderAttributeValues(
        productId: $productId
        attributeId: $attributeId
        moves: $moves
      ) {
        product {
          id
          attributes {
            attribute {
                id
                slug
            }
            values {
                id
            }
          }
        }

        errors {
          field
          message
          code
          attributes
          values
        }
      }
    }
"""


def test_sort_product_attribute_values(
    staff_api_client,
    permission_manage_products,
    product,
    product_type_page_reference_attribute,
):
    staff_api_client.user.user_permissions.add(permission_manage_products)

    product_type = product.product_type

    product_type.product_attributes.clear()
    product_type.product_attributes.add(product_type_page_reference_attribute)

    product_id = graphene.Node.to_global_id("Product", product.id)
    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.id
    )
    attr_values = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                slug=f"{product.pk}_1",
                name="test name 1",
            ),
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                slug=f"{product.pk}_2",
                name="test name 2",
            ),
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                slug=f"{product.pk}_3",
                name="test name 3",
            ),
        ]
    )
    associate_attribute_values_to_instance(
        product, {product_type_page_reference_attribute.pk: attr_values}
    )

    variables = {
        "productId": product_id,
        "attributeId": attribute_id,
        "moves": [
            {
                "id": graphene.Node.to_global_id("AttributeValue", attr_values[0].pk),
                "sortOrder": +1,
            },
            {
                "id": graphene.Node.to_global_id("AttributeValue", attr_values[2].pk),
                "sortOrder": -1,
            },
        ],
    }

    expected_order = [attr_values[1].pk, attr_values[2].pk, attr_values[0].pk]

    content = get_graphql_content(
        staff_api_client.post_graphql(
            PRODUCT_REORDER_ATTRIBUTE_VALUES_MUTATION, variables
        )
    )["data"]["productReorderAttributeValues"]
    assert not content["errors"]

    assert content["product"]["id"] == product_id, "Did not return the correct product"

    gql_attribute_values = content["product"]["attributes"][0]["values"]
    assert len(gql_attribute_values) == 3

    for attr, expected_pk in zip(gql_attribute_values, expected_order):
        db_type, value_pk = graphene.Node.from_global_id(attr["id"])
        assert db_type == "AttributeValue"
        assert int(value_pk) == expected_pk


def test_sort_product_attribute_values_invalid_attribute_id(
    staff_api_client,
    permission_manage_products,
    product,
    product_type_page_reference_attribute,
    color_attribute,
):
    staff_api_client.user.user_permissions.add(permission_manage_products)

    product_type = product.product_type
    product_type.product_attributes.clear()
    product_type.product_attributes.add(product_type_page_reference_attribute)

    product_id = graphene.Node.to_global_id("Product", product.id)
    attr_values = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                slug=f"{product.pk}_1",
                name="test name 1",
            ),
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                slug=f"{product.pk}_2",
                name="test name 2",
            ),
        ]
    )
    associate_attribute_values_to_instance(
        product, {product_type_page_reference_attribute.pk: attr_values}
    )

    variables = {
        "productId": product_id,
        "attributeId": graphene.Node.to_global_id("Attribute", color_attribute.pk),
        "moves": [
            {
                "id": graphene.Node.to_global_id("AttributeValue", attr_values[0].pk),
                "sortOrder": +1,
            },
        ],
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(
            PRODUCT_REORDER_ATTRIBUTE_VALUES_MUTATION, variables
        )
    )["data"]["productReorderAttributeValues"]
    errors = content["errors"]
    assert not content["product"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.NOT_FOUND.name
    assert errors[0]["field"] == "attributeId"


def test_sort_product_attribute_values_invalid_value_id(
    staff_api_client,
    permission_manage_products,
    product,
    product_type_page_reference_attribute,
    size_page_attribute,
):
    staff_api_client.user.user_permissions.add(permission_manage_products)

    product_type = product.product_type
    product_type.product_attributes.clear()
    product_type.product_attributes.add(product_type_page_reference_attribute)

    product_id = graphene.Node.to_global_id("Product", product.id)
    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.id
    )
    attr_values = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                slug=f"{product.pk}_1",
                name="test name 1",
            ),
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                slug=f"{product.pk}_2",
                name="test name 2",
            ),
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                slug=f"{product.pk}_3",
                name="test name 3",
            ),
        ]
    )
    associate_attribute_values_to_instance(
        product, {product_type_page_reference_attribute.pk: attr_values}
    )

    invalid_value_id = graphene.Node.to_global_id(
        "AttributeValue", size_page_attribute.values.first().pk
    )

    variables = {
        "productId": product_id,
        "attributeId": attribute_id,
        "moves": [
            {"id": invalid_value_id, "sortOrder": +1},
            {
                "id": graphene.Node.to_global_id("AttributeValue", attr_values[2].pk),
                "sortOrder": -1,
            },
        ],
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(
            PRODUCT_REORDER_ATTRIBUTE_VALUES_MUTATION, variables
        )
    )["data"]["productReorderAttributeValues"]
    errors = content["errors"]
    assert not content["product"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.NOT_FOUND.name
    assert errors[0]["field"] == "moves"
    assert errors[0]["values"] == [invalid_value_id]


PRODUCT_VARIANT_REORDER_ATTRIBUTE_VALUES_MUTATION = """
    mutation ProductVariantReorderAttributeValues(
      $variantId: ID!
      $attributeId: ID!
      $moves: [ReorderInput!]!
    ) {
      productVariantReorderAttributeValues(
        variantId: $variantId
        attributeId: $attributeId
        moves: $moves
      ) {
        productVariant {
          id
          attributes {
            attribute {
                id
                slug
            }
            values {
                id
            }
          }
        }

        errors {
          field
          message
          code
          attributes
          values
        }
      }
    }
"""


def test_sort_product_variant_attribute_values(
    staff_api_client,
    permission_manage_products,
    product,
    product_type_page_reference_attribute,
):
    staff_api_client.user.user_permissions.add(permission_manage_products)

    variant = product.variants.first()
    product_type = product.product_type
    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(product_type_page_reference_attribute)

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.id
    )
    attr_values = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                slug=f"{variant.pk}_1",
                name="test name 1",
            ),
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                slug=f"{variant.pk}_2",
                name="test name 2",
            ),
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                slug=f"{variant.pk}_3",
                name="test name 3",
            ),
        ]
    )
    associate_attribute_values_to_instance(
        variant, {product_type_page_reference_attribute.pk: attr_values}
    )

    variables = {
        "variantId": variant_id,
        "attributeId": attribute_id,
        "moves": [
            {
                "id": graphene.Node.to_global_id("AttributeValue", attr_values[0].pk),
                "sortOrder": +1,
            },
            {
                "id": graphene.Node.to_global_id("AttributeValue", attr_values[2].pk),
                "sortOrder": -1,
            },
        ],
    }

    expected_order = [attr_values[1].pk, attr_values[2].pk, attr_values[0].pk]

    content = get_graphql_content(
        staff_api_client.post_graphql(
            PRODUCT_VARIANT_REORDER_ATTRIBUTE_VALUES_MUTATION, variables
        )
    )["data"]["productVariantReorderAttributeValues"]
    assert not content["errors"]

    assert (
        content["productVariant"]["id"] == variant_id
    ), "Did not return the correct product variant"

    gql_attribute_values = content["productVariant"]["attributes"][0]["values"]
    assert len(gql_attribute_values) == 3

    for attr, expected_pk in zip(gql_attribute_values, expected_order):
        db_type, value_pk = graphene.Node.from_global_id(attr["id"])
        assert db_type == "AttributeValue"
        assert int(value_pk) == expected_pk


def test_sort_product_variant_attribute_values_invalid_attribute_id(
    staff_api_client,
    permission_manage_products,
    product,
    product_type_page_reference_attribute,
    color_attribute,
):
    staff_api_client.user.user_permissions.add(permission_manage_products)

    variant = product.variants.first()
    product_type = product.product_type
    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(product_type_page_reference_attribute)

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    attr_values = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                slug=f"{variant.pk}_1",
                name="test name 1",
            ),
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                slug=f"{variant.pk}_2",
                name="test name 2",
            ),
        ]
    )
    associate_attribute_values_to_instance(
        variant, {product_type_page_reference_attribute.pk: attr_values}
    )

    variables = {
        "variantId": variant_id,
        "attributeId": graphene.Node.to_global_id("Attribute", color_attribute.pk),
        "moves": [
            {
                "id": graphene.Node.to_global_id("AttributeValue", attr_values[0].pk),
                "sortOrder": +1,
            },
        ],
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(
            PRODUCT_VARIANT_REORDER_ATTRIBUTE_VALUES_MUTATION, variables
        )
    )["data"]["productVariantReorderAttributeValues"]
    errors = content["errors"]
    assert not content["productVariant"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.NOT_FOUND.name
    assert errors[0]["field"] == "attributeId"


def test_sort_product_variant_attribute_values_invalid_value_id(
    staff_api_client,
    permission_manage_products,
    product,
    product_type_page_reference_attribute,
    size_page_attribute,
):
    staff_api_client.user.user_permissions.add(permission_manage_products)

    variant = product.variants.first()
    product_type = product.product_type
    product_type.variant_attributes.clear()
    product_type.variant_attributes.add(product_type_page_reference_attribute)

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.id
    )
    attr_values = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                slug=f"{variant.pk}_1",
                name="test name 1",
            ),
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                slug=f"{variant.pk}_2",
                name="test name 2",
            ),
            AttributeValue(
                attribute=product_type_page_reference_attribute,
                slug=f"{variant.pk}_3",
                name="test name 3",
            ),
        ]
    )
    associate_attribute_values_to_instance(
        variant, {product_type_page_reference_attribute.pk: attr_values}
    )

    invalid_value_id = graphene.Node.to_global_id(
        "AttributeValue", size_page_attribute.values.first().pk
    )

    variables = {
        "variantId": variant_id,
        "attributeId": attribute_id,
        "moves": [
            {"id": invalid_value_id, "sortOrder": +1},
            {
                "id": graphene.Node.to_global_id("AttributeValue", attr_values[2].pk),
                "sortOrder": -1,
            },
        ],
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(
            PRODUCT_VARIANT_REORDER_ATTRIBUTE_VALUES_MUTATION, variables
        )
    )["data"]["productVariantReorderAttributeValues"]
    errors = content["errors"]
    assert not content["productVariant"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.NOT_FOUND.name
    assert errors[0]["field"] == "moves"
    assert errors[0]["values"] == [invalid_value_id]
