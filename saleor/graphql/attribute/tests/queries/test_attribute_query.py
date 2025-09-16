import graphene
import pytest
from django.db.models import Q
from graphene.utils.str_converters import to_camel_case

from .....attribute import AttributeInputType, AttributeType
from .....attribute.models import Attribute
from .....product import ProductTypeKind
from .....product.models import Category, Collection, Product, ProductType
from .....tests.utils import dummy_editorjs
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)


def test_get_single_attribute_by_id_as_customer(
    user_api_client, color_attribute_without_values
):
    attribute_gql_id = graphene.Node.to_global_id(
        "Attribute", color_attribute_without_values.id
    )
    query = """
    query($id: ID!) {
        attribute(id: $id) {
            id
            name
            slug
        }
    }
    """
    content = get_graphql_content(
        user_api_client.post_graphql(query, {"id": attribute_gql_id})
    )

    assert content["data"]["attribute"], "Should have found an attribute"
    assert content["data"]["attribute"]["id"] == attribute_gql_id
    assert content["data"]["attribute"]["slug"] == color_attribute_without_values.slug


def test_get_single_attribute_by_slug_as_customer(
    user_api_client, color_attribute_without_values
):
    attribute_gql_slug = color_attribute_without_values.slug
    query = """
    query($slug: String!) {
        attribute(slug: $slug) {
            id
            name
            slug
        }
    }
    """
    content = get_graphql_content(
        user_api_client.post_graphql(query, {"slug": attribute_gql_slug})
    )

    assert content["data"]["attribute"], "Should have found an attribute"
    assert content["data"]["attribute"]["slug"] == attribute_gql_slug
    assert content["data"]["attribute"]["id"] == graphene.Node.to_global_id(
        "Attribute", color_attribute_without_values.id
    )


QUERY_ATTRIBUTE = """
query ($id: ID!, $query: String) {
  attribute(id: $id) {
    id
    slug
    name
    inputType
    entityType
    referenceTypes {
        __typename
        ... on ProductType {
            id
            slug
        }
        ... on PageType {
            id
            slug
        }
    }
    type
    unit
    choices(first: 10, filter: {search: $query}) {
      edges {
        node {
          slug
          inputType
          value
          file {
            url
            contentType
          }
        }
      }
    }
    valueRequired
    visibleInStorefront
    filterableInStorefront
    filterableInDashboard
    availableInGrid
    storefrontSearchPosition
    translation(languageCode: PL) {
      id
      name
    }
    withChoices
    productTypes(first: 1) {
      edges {
        node {
          id
        }
      }
    }
    productVariantTypes(first: 1) {
      edges {
        node {
          id
        }
      }
    }
    externalReference
  }
}
"""


def test_get_single_product_attribute_by_staff(
    staff_api_client, color_attribute_without_values, permission_manage_products
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    attribute_gql_id = graphene.Node.to_global_id(
        "Attribute", color_attribute_without_values.id
    )
    query = QUERY_ATTRIBUTE
    content = get_graphql_content(
        staff_api_client.post_graphql(query, {"id": attribute_gql_id})
    )

    assert content["data"]["attribute"], "Should have found an attribute"
    assert content["data"]["attribute"]["id"] == attribute_gql_id
    assert content["data"]["attribute"]["slug"] == color_attribute_without_values.slug
    assert (
        content["data"]["attribute"]["valueRequired"]
        == color_attribute_without_values.value_required
    )
    assert (
        content["data"]["attribute"]["visibleInStorefront"]
        == color_attribute_without_values.visible_in_storefront
    )
    assert (
        content["data"]["attribute"]["filterableInStorefront"]
        == color_attribute_without_values.filterable_in_storefront
    )
    assert (
        content["data"]["attribute"]["filterableInDashboard"]
        == color_attribute_without_values.filterable_in_dashboard
    )
    assert (
        content["data"]["attribute"]["availableInGrid"]
        == color_attribute_without_values.available_in_grid
    )
    assert (
        content["data"]["attribute"]["storefrontSearchPosition"]
        == color_attribute_without_values.storefront_search_position
    )


def test_get_single_product_attribute_by_app(
    staff_api_client, color_attribute_without_values, permission_manage_products
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    attribute_gql_id = graphene.Node.to_global_id(
        "Attribute", color_attribute_without_values.id
    )
    query = QUERY_ATTRIBUTE
    content = get_graphql_content(
        staff_api_client.post_graphql(query, {"id": attribute_gql_id})
    )

    assert content["data"]["attribute"], "Should have found an attribute"
    assert content["data"]["attribute"]["id"] == attribute_gql_id
    assert content["data"]["attribute"]["slug"] == color_attribute_without_values.slug
    assert (
        content["data"]["attribute"]["valueRequired"]
        == color_attribute_without_values.value_required
    )
    assert (
        content["data"]["attribute"]["visibleInStorefront"]
        == color_attribute_without_values.visible_in_storefront
    )
    assert (
        content["data"]["attribute"]["filterableInStorefront"]
        == color_attribute_without_values.filterable_in_storefront
    )
    assert (
        content["data"]["attribute"]["filterableInDashboard"]
        == color_attribute_without_values.filterable_in_dashboard
    )
    assert (
        content["data"]["attribute"]["availableInGrid"]
        == color_attribute_without_values.available_in_grid
    )
    assert (
        content["data"]["attribute"]["storefrontSearchPosition"]
        == color_attribute_without_values.storefront_search_position
    )


def test_query_attribute_by_invalid_id(
    staff_api_client, color_attribute_without_values
):
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(QUERY_ATTRIBUTE, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Invalid ID: {id}. Expected: Attribute."
    assert content["data"]["attribute"] is None


def test_query_attribute_with_invalid_object_type(
    staff_api_client, color_attribute_without_values
):
    variables = {
        "id": graphene.Node.to_global_id("Order", color_attribute_without_values.pk)
    }
    response = staff_api_client.post_graphql(QUERY_ATTRIBUTE, variables)
    content = get_graphql_content(response)
    assert content["data"]["attribute"] is None


def test_get_single_product_attribute_by_staff_no_perm(
    staff_api_client, color_attribute_without_values, permission_manage_pages
):
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    attribute_gql_id = graphene.Node.to_global_id(
        "Attribute", color_attribute_without_values.id
    )
    query = QUERY_ATTRIBUTE
    response = staff_api_client.post_graphql(query, {"id": attribute_gql_id})

    assert_no_permission(response)


def test_get_single_page_attribute_by_staff(
    staff_api_client, size_page_attribute, permission_manage_pages
):
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    attribute_gql_id = graphene.Node.to_global_id("Attribute", size_page_attribute.id)
    query = QUERY_ATTRIBUTE
    content = get_graphql_content(
        staff_api_client.post_graphql(query, {"id": attribute_gql_id})
    )

    assert content["data"]["attribute"], "Should have found an attribute"
    assert content["data"]["attribute"]["id"] == attribute_gql_id
    assert content["data"]["attribute"]["slug"] == size_page_attribute.slug


def test_get_single_page_attribute_by_staff_no_perm(
    staff_api_client, size_page_attribute, permission_manage_products
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    attribute_gql_id = graphene.Node.to_global_id("Attribute", size_page_attribute.id)
    query = QUERY_ATTRIBUTE
    response = staff_api_client.post_graphql(query, {"id": attribute_gql_id})

    assert_no_permission(response)


def test_get_single_product_attribute_with_file_value(
    staff_api_client, file_attribute, permission_manage_products, media_root
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    attribute_gql_id = graphene.Node.to_global_id("Attribute", file_attribute.id)
    query = QUERY_ATTRIBUTE
    content = get_graphql_content(
        staff_api_client.post_graphql(query, {"id": attribute_gql_id})
    )
    attribute_data = content["data"]["attribute"]

    assert attribute_data, "Should have found an attribute"
    assert attribute_data["id"] == attribute_gql_id
    assert attribute_data["slug"] == file_attribute.slug
    assert attribute_data["valueRequired"] == file_attribute.value_required
    assert attribute_data["visibleInStorefront"] == file_attribute.visible_in_storefront
    assert (
        attribute_data["filterableInStorefront"]
        == file_attribute.filterable_in_storefront
    )
    assert (
        attribute_data["filterableInDashboard"]
        == file_attribute.filterable_in_dashboard
    )
    assert attribute_data["availableInGrid"] == file_attribute.available_in_grid
    assert (
        attribute_data["storefrontSearchPosition"]
        == file_attribute.storefront_search_position
    )
    assert attribute_data["choices"]["edges"] == []


def test_get_single_reference_attribute_by_staff(
    staff_api_client, product_type_page_reference_attribute, permission_manage_products
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    attribute_gql_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.id
    )
    query = QUERY_ATTRIBUTE
    content = get_graphql_content(
        staff_api_client.post_graphql(query, {"id": attribute_gql_id, "query": ""})
    )

    assert content["data"]["attribute"], "Should have found an attribute"
    assert content["data"]["attribute"]["id"] == attribute_gql_id
    assert (
        content["data"]["attribute"]["slug"]
        == product_type_page_reference_attribute.slug
    )
    assert (
        content["data"]["attribute"]["valueRequired"]
        == product_type_page_reference_attribute.value_required
    )
    assert (
        content["data"]["attribute"]["visibleInStorefront"]
        == product_type_page_reference_attribute.visible_in_storefront
    )
    assert (
        content["data"]["attribute"]["filterableInStorefront"]
        == product_type_page_reference_attribute.filterable_in_storefront
    )
    assert (
        content["data"]["attribute"]["filterableInDashboard"]
        == product_type_page_reference_attribute.filterable_in_dashboard
    )
    assert (
        content["data"]["attribute"]["availableInGrid"]
        == product_type_page_reference_attribute.available_in_grid
    )
    assert (
        content["data"]["attribute"]["storefrontSearchPosition"]
        == product_type_page_reference_attribute.storefront_search_position
    )
    assert (
        content["data"]["attribute"]["entityType"]
        == product_type_page_reference_attribute.entity_type.upper()
    )
    assert not content["data"]["attribute"]["choices"]["edges"]


def test_get_single_numeric_attribute_by_staff(
    staff_api_client, numeric_attribute, permission_manage_products
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    attribute_gql_id = graphene.Node.to_global_id("Attribute", numeric_attribute.id)
    query = QUERY_ATTRIBUTE
    content = get_graphql_content(
        staff_api_client.post_graphql(query, {"id": attribute_gql_id})
    )

    assert content["data"]["attribute"], "Should have found an attribute"
    assert content["data"]["attribute"]["id"] == attribute_gql_id
    assert content["data"]["attribute"]["slug"] == numeric_attribute.slug
    assert (
        content["data"]["attribute"]["inputType"]
        == numeric_attribute.input_type.upper()
    )
    assert content["data"]["attribute"]["unit"] == numeric_attribute.unit.upper()
    assert (
        content["data"]["attribute"]["valueRequired"]
        == numeric_attribute.value_required
    )
    assert (
        content["data"]["attribute"]["visibleInStorefront"]
        == numeric_attribute.visible_in_storefront
    )
    assert (
        content["data"]["attribute"]["filterableInStorefront"]
        == numeric_attribute.filterable_in_storefront
    )
    assert (
        content["data"]["attribute"]["filterableInDashboard"]
        == numeric_attribute.filterable_in_dashboard
    )
    assert (
        content["data"]["attribute"]["availableInGrid"]
        == numeric_attribute.available_in_grid
    )
    assert (
        content["data"]["attribute"]["storefrontSearchPosition"]
        == numeric_attribute.storefront_search_position
    )


def test_get_single_swatch_attribute_by_staff(
    staff_api_client, swatch_attribute, permission_manage_products
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    attribute_gql_id = graphene.Node.to_global_id("Attribute", swatch_attribute.id)
    query = QUERY_ATTRIBUTE
    content = get_graphql_content(
        staff_api_client.post_graphql(query, {"id": attribute_gql_id})
    )

    assert content["data"]["attribute"], "Should have found an attribute"
    assert content["data"]["attribute"]["id"] == attribute_gql_id
    assert content["data"]["attribute"]["slug"] == swatch_attribute.slug
    assert (
        content["data"]["attribute"]["inputType"] == swatch_attribute.input_type.upper()
    )
    assert content["data"]["attribute"]["unit"] is None
    assert (
        content["data"]["attribute"]["valueRequired"] == swatch_attribute.value_required
    )
    assert (
        content["data"]["attribute"]["visibleInStorefront"]
        == swatch_attribute.visible_in_storefront
    )
    assert (
        content["data"]["attribute"]["filterableInStorefront"]
        == swatch_attribute.filterable_in_storefront
    )
    assert (
        content["data"]["attribute"]["filterableInDashboard"]
        == swatch_attribute.filterable_in_dashboard
    )
    assert (
        content["data"]["attribute"]["availableInGrid"]
        == swatch_attribute.available_in_grid
    )
    assert (
        content["data"]["attribute"]["storefrontSearchPosition"]
        == swatch_attribute.storefront_search_position
    )
    assert (
        len(content["data"]["attribute"]["choices"]["edges"])
        == swatch_attribute.values.all().count()
    )
    attribute_value_data = []
    for value in swatch_attribute.values.all():
        data = {
            "node": {
                "slug": value.slug,
                "value": value.value,
                "inputType": value.input_type.upper(),
                "file": (
                    {"url": value.file_url, "contentType": value.content_type}
                    if value.file_url
                    else None
                ),
            }
        }
        attribute_value_data.append(data)

    for data in attribute_value_data:
        assert data in content["data"]["attribute"]["choices"]["edges"]


def test_get_single_reference_product_attribute_with_reference_types(
    staff_api_client,
    product_type_product_single_reference_attribute,
    product_type,
    product_type_with_product_attributes,
    product_type_with_variant_attributes,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    attribute = product_type_product_single_reference_attribute
    reference_product_types = [product_type, product_type_with_product_attributes]
    attribute.reference_product_types.add(*reference_product_types)

    query = QUERY_ATTRIBUTE
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {"id": attribute_id}

    # when
    content = get_graphql_content(staff_api_client.post_graphql(query, variables))

    # then
    attribute_data = content["data"]["attribute"]

    assert attribute_data["id"] == attribute_id
    assert attribute_data["slug"] == attribute.slug

    reference_types = attribute_data["referenceTypes"]
    assert len(reference_types) == len(reference_product_types)
    assert {type["slug"] for type in reference_types} == {
        product_type.slug for product_type in reference_product_types
    }


def test_get_single_reference_variant_attribute_with_reference_types(
    staff_api_client,
    product_type_variant_single_reference_attribute,
    product_type,
    product_type_with_product_attributes,
    product_type_with_variant_attributes,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    attribute = product_type_variant_single_reference_attribute
    reference_product_types = [product_type, product_type_with_product_attributes]
    attribute.reference_product_types.add(*reference_product_types)

    query = QUERY_ATTRIBUTE
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {"id": attribute_id}

    # when
    content = get_graphql_content(staff_api_client.post_graphql(query, variables))

    # then
    attribute_data = content["data"]["attribute"]

    assert attribute_data["id"] == attribute_id
    assert attribute_data["slug"] == attribute.slug

    reference_types = attribute_data["referenceTypes"]
    assert len(reference_types) == len(reference_product_types)
    assert {ref_type["slug"] for ref_type in reference_types} == {
        product_type.slug for product_type in reference_product_types
    }


def test_get_single_reference_page_attribute_with_reference_types(
    staff_api_client,
    product_type_page_single_reference_attribute,
    page_type_list,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    attribute = product_type_page_single_reference_attribute
    reference_page_types = page_type_list[:2]
    attribute.reference_page_types.add(*reference_page_types)

    query = QUERY_ATTRIBUTE
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {"id": attribute_id}

    # when
    content = get_graphql_content(staff_api_client.post_graphql(query, variables))

    # then
    attribute_data = content["data"]["attribute"]

    assert attribute_data["id"] == attribute_id
    assert attribute_data["slug"] == attribute.slug

    reference_types = attribute_data["referenceTypes"]
    assert len(reference_types) == len(reference_page_types)
    assert {type["slug"] for type in reference_types} == {
        product_type.slug for product_type in reference_page_types
    }


def test_get_reference_product_attribute_with_reference_types(
    staff_api_client,
    product_type_product_reference_attribute,
    product_type,
    product_type_with_product_attributes,
    product_type_with_variant_attributes,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    attribute = product_type_product_reference_attribute
    reference_product_types = [product_type, product_type_with_product_attributes]
    attribute.reference_product_types.add(*reference_product_types)

    query = QUERY_ATTRIBUTE
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {"id": attribute_id}

    # when
    content = get_graphql_content(staff_api_client.post_graphql(query, variables))

    # then
    attribute_data = content["data"]["attribute"]

    assert attribute_data["id"] == attribute_id
    assert attribute_data["slug"] == attribute.slug

    reference_types = attribute_data["referenceTypes"]
    assert len(reference_types) == len(reference_product_types)
    assert {type["slug"] for type in reference_types} == {
        product_type.slug for product_type in reference_product_types
    }


def test_get_reference_variant_attribute_with_reference_types(
    staff_api_client,
    product_type_variant_reference_attribute,
    product_type,
    product_type_with_product_attributes,
    product_type_with_variant_attributes,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    attribute = product_type_variant_reference_attribute
    reference_product_types = [product_type, product_type_with_product_attributes]
    attribute.reference_product_types.add(*reference_product_types)

    query = QUERY_ATTRIBUTE
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {"id": attribute_id}

    # when
    content = get_graphql_content(staff_api_client.post_graphql(query, variables))

    # then
    attribute_data = content["data"]["attribute"]

    assert attribute_data["id"] == attribute_id
    assert attribute_data["slug"] == attribute.slug

    reference_types = attribute_data["referenceTypes"]
    assert len(reference_types) == len(reference_product_types)
    assert {type["slug"] for type in reference_types} == {
        product_type.slug for product_type in reference_product_types
    }


def test_get_reference_page_attribute_with_reference_types(
    staff_api_client,
    product_type_page_reference_attribute,
    page_type_list,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    attribute = product_type_page_reference_attribute
    reference_page_types = page_type_list[:2]
    attribute.reference_page_types.add(*reference_page_types)

    query = QUERY_ATTRIBUTE
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {"id": attribute_id}

    # when
    content = get_graphql_content(staff_api_client.post_graphql(query, variables))

    # then
    attribute_data = content["data"]["attribute"]

    assert attribute_data["id"] == attribute_id
    assert attribute_data["slug"] == attribute.slug

    reference_types = attribute_data["referenceTypes"]
    assert len(reference_types) == len(reference_page_types)
    assert {type["slug"] for type in reference_types} == {
        product_type.slug for product_type in reference_page_types
    }


def test_get_reference_collection_attribute(
    staff_api_client,
    product_type_collection_reference_attribute,
    product_type,
    product_type_with_product_attributes,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    attribute = product_type_collection_reference_attribute
    reference_product_types = [product_type, product_type_with_product_attributes]
    attribute.reference_product_types.add(*reference_product_types)

    query = QUERY_ATTRIBUTE
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {"id": attribute_id}

    # when
    content = get_graphql_content(staff_api_client.post_graphql(query, variables))

    # then
    attribute_data = content["data"]["attribute"]
    assert attribute_data["id"] == attribute_id
    assert attribute_data["slug"] == attribute.slug

    assert not attribute_data["referenceTypes"]


def test_get_reference_category_attribute(
    staff_api_client,
    product_type_category_reference_attribute,
    product_type,
    product_type_with_product_attributes,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    attribute = product_type_category_reference_attribute
    reference_product_types = [product_type, product_type_with_product_attributes]
    attribute.reference_product_types.add(*reference_product_types)

    query = QUERY_ATTRIBUTE
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {"id": attribute_id}

    # when
    content = get_graphql_content(staff_api_client.post_graphql(query, variables))

    # then
    attribute_data = content["data"]["attribute"]
    assert attribute_data["id"] == attribute_id
    assert attribute_data["slug"] == attribute.slug

    assert not attribute_data["referenceTypes"]


QUERY_ATTRIBUTE_REFERENCE_TYPES = """
    query ($id: ID!, $limit: PositiveInt) {
        attribute(id: $id) {
            id
            name
            slug
            referenceTypes(limit: $limit) {
                ... on ProductType {
                    id
                    name
                    slug
                }
                ... on PageType {
                    id
                    name
                    slug
                }
            }
        }
    }
"""


def test_get_attribute_reference_product_types_with_limit(
    staff_api_client,
    product_type_product_reference_attribute,
    product_type,
    product_type_with_product_attributes,
    product_type_with_variant_attributes,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    attribute = product_type_product_reference_attribute
    reference_product_types = [
        product_type,
        product_type_with_product_attributes,
        product_type_with_variant_attributes,
    ]
    attribute.reference_product_types.add(*reference_product_types)

    query = QUERY_ATTRIBUTE_REFERENCE_TYPES
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    # limit smaller than the number of reference types
    limit = 2
    variables = {"id": attribute_id, "limit": limit}

    # when
    content = get_graphql_content(staff_api_client.post_graphql(query, variables))

    # then
    attribute_data = content["data"]["attribute"]
    assert attribute_data["id"] == attribute_id
    assert attribute_data["slug"] == attribute.slug

    reference_types = attribute_data["referenceTypes"]
    assert len(reference_types) == limit


def test_get_attribute_reference_product_types_limit_exceeded(
    staff_api_client,
    product_type_product_reference_attribute,
    product_type,
    product_type_with_product_attributes,
    product_type_with_variant_attributes,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    attribute = product_type_product_reference_attribute
    reference_product_types = [
        product_type,
        product_type_with_product_attributes,
        product_type_with_variant_attributes,
    ]
    attribute.reference_product_types.add(*reference_product_types)

    query = QUERY_ATTRIBUTE_REFERENCE_TYPES
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    limit = 0
    variables = {"id": attribute_id, "limit": limit}

    # when
    content = get_graphql_content_from_response(
        staff_api_client.post_graphql(query, variables)
    )

    # then
    assert len(content["errors"]) == 1
    assert (
        f'Variable "$limit" got invalid value {limit}'
        in content["errors"][0]["message"]
    )


def test_get_attribute_reference_page_types_with_limit(
    staff_api_client,
    product_type_page_reference_attribute,
    page_type_list,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    attribute = product_type_page_reference_attribute
    attribute.reference_page_types.add(*page_type_list)

    query = QUERY_ATTRIBUTE_REFERENCE_TYPES
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    # limit smaller than the number of reference types
    limit = 2
    variables = {"id": attribute_id, "limit": limit}

    # when
    content = get_graphql_content(staff_api_client.post_graphql(query, variables))

    # then
    attribute_data = content["data"]["attribute"]
    assert attribute_data["id"] == attribute_id
    assert attribute_data["slug"] == attribute.slug

    reference_types = attribute_data["referenceTypes"]
    assert len(reference_types) == limit


def test_get_attribute_reference_page_types_invalid_limit(
    staff_api_client,
    product_type_page_reference_attribute,
    page_type_list,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    attribute = product_type_page_reference_attribute
    attribute.reference_page_types.add(*page_type_list)

    query = QUERY_ATTRIBUTE_REFERENCE_TYPES
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    limit = 0
    variables = {"id": attribute_id, "limit": limit}

    # when
    content = get_graphql_content_from_response(
        staff_api_client.post_graphql(query, variables)
    )

    # then
    assert len(content["errors"]) == 1
    assert (
        f'Variable "$limit" got invalid value {limit}'
        in content["errors"][0]["message"]
    )


QUERY_ATTRIBUTES = """
    query {
        attributes(first: 20) {
            edges {
                node {
                    id
                    name
                    slug
                    choices(first: 10) {
                        edges {
                            node {
                            id
                            name
                            slug
                            inputType
                            value
                            file {
                                url
                                contentType
                            }
                            translation(languageCode: PL) {
                                id
                                name
                                translatableContent {
                                id
                                }
                            }
                            reference
                            richText
                            plainText
                            boolean
                            date
                            dateTime
                            externalReference
                            }
                        }
                    }
                }
            }
        }
    }
"""


def test_attributes_query(user_api_client, product):
    attributes = Attribute.objects
    query = QUERY_ATTRIBUTES
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    attributes_data = content["data"]["attributes"]["edges"]
    assert attributes_data
    assert len(attributes_data) == attributes.count()


def test_attributes_query_hidden_attribute(user_api_client, product, color_attribute):
    query = QUERY_ATTRIBUTES

    # hide the attribute
    color_attribute.visible_in_storefront = False
    color_attribute.save(update_fields=["visible_in_storefront"])

    attribute_count = Attribute.objects.get_visible_to_user(
        user_api_client.user
    ).count()
    assert attribute_count == 1

    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    attributes_data = content["data"]["attributes"]["edges"]
    assert len(attributes_data) == attribute_count


def test_attributes_query_hidden_attribute_as_staff_user_without_permissions(
    staff_api_client, product, color_attribute
):
    query = QUERY_ATTRIBUTES

    # hide the attribute
    color_attribute.visible_in_storefront = False
    color_attribute.save(update_fields=["visible_in_storefront"])

    attribute_count = Attribute.objects.all().count()

    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    attributes_data = content["data"]["attributes"]["edges"]
    assert len(attributes_data) == attribute_count - 1  # invisible doesn't count


def test_attributes_query_hidden_attribute_as_staff_user_with_permissions(
    staff_api_client,
    product,
    color_attribute,
    permission_manage_product_types_and_attributes,
):
    query = QUERY_ATTRIBUTES

    # hide the attribute
    color_attribute.visible_in_storefront = False
    color_attribute.save(update_fields=["visible_in_storefront"])

    attribute_count = Attribute.objects.all().count()

    response = staff_api_client.post_graphql(
        query,
        permissions=[permission_manage_product_types_and_attributes],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    attributes_data = content["data"]["attributes"]["edges"]
    assert len(attributes_data) == attribute_count


NOT_EXISTS_IDS_ATTRIBUTES_QUERY = """
    query ($filter: AttributeFilterInput!) {
        attributes(first: 5, filter: $filter) {
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
"""


def test_attributes_query_ids_not_exists(user_api_client, category):
    query = NOT_EXISTS_IDS_ATTRIBUTES_QUERY
    variables = {"filter": {"ids": ["ygRqjpmXYqaTD9r=", "PBa4ZLBhnXHSz6v="]}}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response, ignore_errors=True)
    message_error = '{"ids": [{"message": "Invalid ID specified.", "code": ""}]}'

    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == message_error
    assert content["data"]["attributes"] is None


@pytest.mark.parametrize(
    ("attribute", "expected_value"),
    [
        ("filterable_in_storefront", True),
        ("filterable_in_dashboard", True),
        ("visible_in_storefront", True),
        ("available_in_grid", True),
        ("value_required", False),
        ("storefront_search_position", 0),
    ],
)
def test_retrieving_the_restricted_attributes_restricted(
    staff_api_client,
    color_attribute,
    permission_manage_products,
    attribute,
    expected_value,
):
    attribute = to_camel_case(attribute)
    query = f"""
        {{
          attributes(first: 10) {{
            edges {{
              node {{
                {attribute}
              }}
            }}
          }}
        }}
    """

    found_attributes = get_graphql_content(
        staff_api_client.post_graphql(query, permissions=[permission_manage_products])
    )["data"]["attributes"]["edges"]

    assert len(found_attributes) == 1
    assert found_attributes[0]["node"][attribute] == expected_value


@pytest.mark.parametrize("tested_field", ["inCategory", "inCollection"])
def test_attributes_in_collection_query(
    user_api_client,
    product_type,
    category,
    published_collection,
    collection_with_products,
    tested_field,
    channel_USD,
):
    if "Collection" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id(
            "Collection", published_collection.pk
        )
    elif "Category" in tested_field:
        filtered_by_node_id = graphene.Node.to_global_id("Category", category.pk)
    else:
        raise AssertionError(tested_field)
    expected_qs = Attribute.objects.filter(
        Q(attributeproduct__product_type_id=product_type.pk)
        | Q(attributevariant__product_type_id=product_type.pk)
    )

    # Create another product type and attribute that shouldn't get matched
    other_category = Category.objects.create(name="Other Category", slug="other-cat")
    other_attribute = Attribute.objects.create(name="Other", slug="other")
    other_product_type = ProductType.objects.create(
        name="Other type",
        has_variants=True,
        is_shipping_required=True,
        kind=ProductTypeKind.NORMAL,
    )
    other_product_type.product_attributes.add(other_attribute)
    other_product = Product.objects.create(
        name="Another Product", product_type=other_product_type, category=other_category
    )

    # Create another collection with products but shouldn't get matched
    # as we don't look for this other collection
    other_collection = Collection.objects.create(
        name="Other Collection",
        slug="other-collection",
        description=dummy_editorjs("Test description"),
    )
    other_collection.products.add(other_product)

    query = """
    query($nodeID: ID!, $channel: String) {
        attributes(first: 20, %(filter_input)s) {
            edges {
                node {
                    id
                    name
                    slug
                }
            }
        }
    }
    """

    query = query % {
        "filter_input": f"filter: {{ {tested_field}: $nodeID }} channel: $channel"
    }

    variables = {"nodeID": filtered_by_node_id, "channel": channel_USD.slug}
    content = get_graphql_content(user_api_client.post_graphql(query, variables))
    attributes_data = content["data"]["attributes"]["edges"]

    flat_attributes_data = [attr["node"]["slug"] for attr in attributes_data]
    expected_flat_attributes_data = list(expected_qs.values_list("slug", flat=True))

    assert flat_attributes_data == expected_flat_attributes_data


@pytest.mark.parametrize(
    ("input_type", "expected_with_choice_return"),
    [
        (AttributeInputType.DROPDOWN, True),
        (AttributeInputType.MULTISELECT, True),
        (AttributeInputType.FILE, False),
        (AttributeInputType.REFERENCE, False),
        (AttributeInputType.NUMERIC, False),
        (AttributeInputType.RICH_TEXT, False),
        (AttributeInputType.BOOLEAN, False),
    ],
)
def test_attributes_with_choice_flag(
    user_api_client,
    input_type,
    expected_with_choice_return,
):
    attribute = Attribute.objects.create(
        slug=input_type,
        name=input_type.upper(),
        type=AttributeType.PRODUCT_TYPE,
        input_type=input_type,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )

    attribute_gql_id = graphene.Node.to_global_id("Attribute", attribute.id)
    query = """
    query($id: ID!) {
        attribute(id: $id) {
            id
            inputType
            withChoices

        }
    }
    """
    content = get_graphql_content(
        user_api_client.post_graphql(query, {"id": attribute_gql_id})
    )
    assert content["data"]["attribute"]["id"] == attribute_gql_id
    assert content["data"]["attribute"]["inputType"] == input_type.upper().replace(
        "-", "_"
    )
    assert content["data"]["attribute"]["withChoices"] == expected_with_choice_return


QUERY_ATTRIBUTE_BY_EXTERNAL_REFERENCE = """
    query($id: ID, $externalReference: String) {
        attribute(id: $id, externalReference: $externalReference) {
            id
            externalReference
        }
    }
"""


def test_get_attribute_by_external_reference(
    staff_api_client, color_attribute_without_values, permission_manage_products
):
    # given
    attribute = color_attribute_without_values
    ext_ref = "test-ext-id"
    attribute.external_reference = ext_ref
    attribute.save(update_fields=["external_reference"])
    variables = {"externalReference": ext_ref}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ATTRIBUTE_BY_EXTERNAL_REFERENCE,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["attribute"]
    assert data["externalReference"] == ext_ref
    assert data["id"] == graphene.Node.to_global_id("Attribute", attribute.id)


QUERY_ATTRIBUTE_TWO_LIMITS = """
    query($id: ID, $limit1: PositiveInt, $limit2: PositiveInt) {
        limit1: attribute(id: $id) {
            id
            name
            slug
            referenceTypes(limit: $limit1) {
                ... on ProductType {
                    id
                    name
                }
                ... on PageType {
                    id
                    name
                }
            }
        }
        limit2: attribute(id: $id) {
            id
            name
            slug
            referenceTypes(limit: $limit2) {
                ... on ProductType {
                    id
                    name
                }
                ... on PageType {
                    id
                    name
                }
            }
        }
    }
"""


def test_get_reference_product_attribute_with_reference_types_and_different_limits(
    staff_api_client,
    product_type_product_reference_attribute,
    product_type,
    product_type_with_product_attributes,
    product_type_with_variant_attributes,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    attribute = product_type_product_reference_attribute
    reference_product_types = [product_type, product_type_with_product_attributes]
    attribute.reference_product_types.add(*reference_product_types)

    query = QUERY_ATTRIBUTE_TWO_LIMITS
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    limit1 = 1
    limit2 = 2
    variables = {"id": attribute_id, "limit1": limit1, "limit2": limit2}

    # when
    content = get_graphql_content(staff_api_client.post_graphql(query, variables))

    # then
    attribute_data = content["data"]
    limit1_data = attribute_data["limit1"]
    limit2_data = attribute_data["limit2"]

    assert limit1_data["id"] == attribute_id
    assert limit1_data["slug"] == attribute.slug

    reference_types = limit1_data["referenceTypes"]
    assert len(reference_types) == limit1

    assert limit2_data["id"] == attribute_id
    assert limit2_data["slug"] == attribute.slug

    reference_types = limit2_data["referenceTypes"]
    assert len(reference_types) == limit2
