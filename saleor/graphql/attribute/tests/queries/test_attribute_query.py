import graphene
import pytest
from django.db.models import Q
from graphene.utils.str_converters import to_camel_case

from .....attribute.models import Attribute
from .....product.models import Category, Collection, Product, ProductType
from ....tests.utils import assert_no_permission, get_graphql_content


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
query($id: ID!) {
    attribute(id: $id) {
        id
        slug
        name
        inputType
        entityType
        type
        values {
            slug
            inputType
            file {
                url
                contentType
            }
        }
        valueRequired
        visibleInStorefront
        filterableInStorefront
        filterableInDashboard
        availableInGrid
        storefrontSearchPosition
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
    assert len(attribute_data["values"]) == file_attribute.values.count()
    attribute_value_data = []
    for value in file_attribute.values.all():
        data = {
            "slug": value.slug,
            "inputType": value.input_type.upper(),
            "file": {"url": value.file_url, "contentType": value.content_type},
        }
        attribute_value_data.append(data)

    for data in attribute_value_data:
        assert data in attribute_data["values"]


def test_get_single_reference_attribute_by_staff(
    staff_api_client, product_type_page_reference_attribute, permission_manage_products
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    attribute_gql_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.id
    )
    query = QUERY_ATTRIBUTE
    content = get_graphql_content(
        staff_api_client.post_graphql(query, {"id": attribute_gql_id})
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


QUERY_ATTRIBUTES = """
    query {
        attributes(first: 20) {
            edges {
                node {
                    id
                    name
                    slug
                    values {
                        id
                        name
                        slug
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


def test_attributes_query_hidden_attribute_as_staff_user(
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
    "attribute, expected_value",
    (
        ("filterable_in_storefront", True),
        ("filterable_in_dashboard", True),
        ("visible_in_storefront", True),
        ("available_in_grid", True),
        ("value_required", False),
        ("storefront_search_position", 0),
    ),
)
def test_retrieving_the_restricted_attributes_restricted(
    staff_api_client,
    color_attribute,
    permission_manage_products,
    attribute,
    expected_value,
):
    """Checks if the attributes are restricted and if their default value
    is the expected one."""

    attribute = to_camel_case(attribute)
    query = (
        """
        {
          attributes(first: 10) {
            edges {
              node {
                %s
              }
            }
          }
        }
    """
        % attribute
    )

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
        name="Other type", has_variants=True, is_shipping_required=True
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
        description="Description",
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
        "filter_input": "filter: { %s: $nodeID, channel: $channel }" % tested_field
    }

    variables = {"nodeID": filtered_by_node_id, "channel": channel_USD.slug}
    content = get_graphql_content(user_api_client.post_graphql(query, variables))
    attributes_data = content["data"]["attributes"]["edges"]

    flat_attributes_data = [attr["node"]["slug"] for attr in attributes_data]
    expected_flat_attributes_data = list(expected_qs.values_list("slug", flat=True))

    assert flat_attributes_data == expected_flat_attributes_data
