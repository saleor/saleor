from unittest.mock import patch

import graphene
import pytest

from ....product.error_codes import ProductErrorCode
from ....product.models import ProductType
from ...tests.utils import get_graphql_content
from ..enums import ProductTypeKindEnum

PRODUCT_TYPE_UPDATE_MUTATION = """
mutation updateProductType(
    $id: ID!,
    $name: String!,
    $hasVariants: Boolean!,
    $isShippingRequired: Boolean!,
    $productAttributes: [ID!],
    ) {
        productTypeUpdate(
        id: $id,
        input: {
            name: $name,
            hasVariants: $hasVariants,
            isShippingRequired: $isShippingRequired,
            productAttributes: $productAttributes
        }) {
            productType {
                name
                slug
                isShippingRequired
                hasVariants
                variantAttributes {
                    id
                }
                productAttributes {
                    id
                }
            }
            errors {
                code
                field
                attributes
            }
            }
        }
"""


def test_product_type_update_mutation(
    staff_api_client,
    product_type,
    product,
    permission_manage_product_types_and_attributes,
):
    query = PRODUCT_TYPE_UPDATE_MUTATION
    product_type_name = "test type updated"
    slug = product_type.slug
    has_variants = True
    require_shipping = False
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)

    # Test scenario: remove all product attributes using [] as input
    # but do not change variant attributes
    product_attributes = []
    product_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in product_attributes
    ]
    variant_attributes = product_type.variant_attributes.all()

    variables = {
        "id": product_type_id,
        "name": product_type_name,
        "hasVariants": has_variants,
        "isShippingRequired": require_shipping,
        "productAttributes": product_attributes_ids,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeUpdate"]["productType"]
    assert data["name"] == product_type_name
    assert data["slug"] == slug
    assert data["hasVariants"] == has_variants
    assert data["isShippingRequired"] == require_shipping
    assert not data["productAttributes"]
    assert len(data["variantAttributes"]) == (variant_attributes.count())


def test_product_type_update_mutation_not_valid_attributes(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    size_page_attribute,
):
    # given
    query = PRODUCT_TYPE_UPDATE_MUTATION
    product_type_name = "test type updated"
    has_variants = True
    require_shipping = False
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)

    # Test scenario: adding page attribute raise error

    page_attribute_id = graphene.Node.to_global_id("Attribute", size_page_attribute.id)
    product_attributes_ids = [
        page_attribute_id,
        graphene.Node.to_global_id(
            "Attribute", product_type.product_attributes.first().pk
        ),
    ]

    variables = {
        "id": product_type_id,
        "name": product_type_name,
        "hasVariants": has_variants,
        "isShippingRequired": require_shipping,
        "productAttributes": product_attributes_ids,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productTypeUpdate"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "productAttributes"
    assert errors[0]["code"] == ProductErrorCode.INVALID.name
    assert errors[0]["attributes"] == [page_attribute_id]


UPDATE_PRODUCT_TYPE_SLUG_MUTATION = """
    mutation($id: ID!, $slug: String) {
        productTypeUpdate(
            id: $id
            input: {
                slug: $slug
            }
        ) {
            productType{
                name
                slug
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


@pytest.mark.parametrize(
    "input_slug, expected_slug, error_message",
    [
        ("test-slug", "test-slug", None),
        ("", "", "Slug value cannot be blank."),
        (None, "", "Slug value cannot be blank."),
    ],
)
@patch("saleor.product.search.update_products_search_vector")
def test_update_product_type_slug(
    update_products_search_vector_mock,
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    input_slug,
    expected_slug,
    error_message,
):
    query = UPDATE_PRODUCT_TYPE_SLUG_MUTATION
    old_slug = product_type.slug

    assert old_slug != input_slug

    node_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeUpdate"]
    errors = data["errors"]
    if not error_message:
        assert not errors
        assert data["productType"]["slug"] == expected_slug
        update_products_search_vector_mock.assert_not_called()
    else:
        assert errors
        assert errors[0]["field"] == "slug"
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


def test_update_product_type_slug_exists(
    staff_api_client, product_type, permission_manage_product_types_and_attributes
):
    query = UPDATE_PRODUCT_TYPE_SLUG_MUTATION
    input_slug = "test-slug"

    second_product_type = ProductType.objects.get(pk=product_type.pk)
    second_product_type.pk = None
    second_product_type.slug = input_slug
    second_product_type.save()

    assert input_slug != product_type.slug

    node_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeUpdate"]
    errors = data["errors"]
    assert errors
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == ProductErrorCode.UNIQUE.name


@pytest.mark.parametrize(
    "input_slug, expected_slug, input_name, error_message, error_field",
    [
        ("test-slug", "test-slug", "New name", None, None),
        ("", "", "New name", "Slug value cannot be blank.", "slug"),
        (None, "", "New name", "Slug value cannot be blank.", "slug"),
        ("test-slug", "", None, "This field cannot be blank.", "name"),
        ("test-slug", "", "", "This field cannot be blank.", "name"),
        (None, None, None, "Slug value cannot be blank.", "slug"),
    ],
)
def test_update_product_type_slug_and_name(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    input_slug,
    expected_slug,
    input_name,
    error_message,
    error_field,
):
    query = """
            mutation($id: ID!, $name: String, $slug: String) {
            productTypeUpdate(
                id: $id
                input: {
                    name: $name
                    slug: $slug
                }
            ) {
                productType{
                    name
                    slug
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """

    old_name = product_type.name
    old_slug = product_type.slug

    assert input_slug != old_slug
    assert input_name != old_name

    node_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"slug": input_slug, "name": input_name, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    product_type.refresh_from_db()
    data = content["data"]["productTypeUpdate"]
    errors = data["errors"]
    if not error_message:
        assert data["productType"]["name"] == input_name == product_type.name
        assert data["productType"]["slug"] == input_slug == product_type.slug
    else:
        assert errors
        assert errors[0]["field"] == error_field
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


def test_update_product_type_with_negative_weight(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
):
    query = """
        mutation($id: ID!, $weight: WeightScalar) {
            productTypeUpdate(
                id: $id
                input: {
                    weight: $weight
                }
            ) {
                productType{
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

    node_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"id": node_id, "weight": "-1"}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    product_type.refresh_from_db()
    data = content["data"]["productTypeUpdate"]
    error = data["errors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


def test_update_product_type_kind(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
):
    query = """
        mutation($id: ID!, $kind: ProductTypeKindEnum) {
            productTypeUpdate(id: $id, input: { kind: $kind }) {
                productType{
                    name
                    kind
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """
    kind = ProductTypeKindEnum.GIFT_CARD.name
    assert product_type.kind != kind

    node_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"kind": kind, "id": node_id}

    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_product_types_and_attributes],
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["productType"]["kind"] == kind


def test_update_product_type_kind_omitted(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
):
    query = """
        mutation($id: ID!, $name: String) {
            productTypeUpdate(id: $id, input: { name: $name }) {
                productType{
                    name
                    kind
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """
    assert product_type.kind == ProductTypeKindEnum.NORMAL.value
    name = "New name"
    node_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"id": node_id, "name": name}

    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_product_types_and_attributes],
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["productType"]["kind"] == ProductTypeKindEnum.NORMAL.name
    assert data["productType"]["name"] == name


@patch("saleor.product.tasks.update_variants_names.delay")
def test_product_type_update_changes_variant_name(
    mock_update_variants_names,
    staff_api_client,
    product_type,
    product,
    permission_manage_product_types_and_attributes,
):
    query = """
    mutation updateProductType(
        $id: ID!,
        $hasVariants: Boolean!,
        $isShippingRequired: Boolean!,
        $variantAttributes: [ID!],
        ) {
            productTypeUpdate(
            id: $id,
            input: {
                hasVariants: $hasVariants,
                isShippingRequired: $isShippingRequired,
                variantAttributes: $variantAttributes}) {
                productType {
                    id
                }
              }
            }
    """
    variant = product.variants.first()
    variant.name = "test name"
    variant.save()
    has_variants = True
    require_shipping = False
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)

    variant_attributes = product_type.variant_attributes.all()
    variant_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in variant_attributes
    ]
    variables = {
        "id": product_type_id,
        "hasVariants": has_variants,
        "isShippingRequired": require_shipping,
        "variantAttributes": variant_attributes_ids,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    get_graphql_content(response)
    variant_attributes = set(variant_attributes)
    variant_attributes_ids = [attr.pk for attr in variant_attributes]
    mock_update_variants_names.assert_called_once_with(
        product_type.pk, variant_attributes_ids
    )
