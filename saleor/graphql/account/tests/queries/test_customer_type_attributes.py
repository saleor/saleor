import graphene

from ....tests.utils import assert_no_permission, get_graphql_content

CUSTOMER_TYPE_ATTRIBUTES_QUERY = """
    query CustomerType($id: ID!) {
        customerType(id: $id) {
            id
            attributes {
                slug
            }
        }
    }
"""

CUSTOMER_TYPE_AVAILABLE_ATTRIBUTES_QUERY = """
    query CustomerType(
        $id: ID!, $where: AttributeWhereInput, $search: String
    ) {
        customerType(id: $id) {
            id
            availableAttributes(first: 10, where: $where, search: $search) {
                edges {
                    node {
                        slug
                    }
                }
                totalCount
            }
        }
    }
"""


def test_attributes_with_manage_permission_includes_hidden(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
    loyalty_customer_attribute,
    hidden_customer_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    customer_type.customer_attributes.add(
        loyalty_customer_attribute, hidden_customer_attribute
    )
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_ATTRIBUTES_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["customerType"]["attributes"]
    assert {attr["slug"] for attr in attributes} == {
        loyalty_customer_attribute.slug,
        hidden_customer_attribute.slug,
    }


def test_attributes_without_manage_permission_hides_storefront_invisible(
    staff_api_client,
    customer_type,
    loyalty_customer_attribute,
    hidden_customer_attribute,
):
    # given
    customer_type.customer_attributes.add(
        loyalty_customer_attribute, hidden_customer_attribute
    )
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_ATTRIBUTES_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["customerType"]["attributes"]
    assert [attr["slug"] for attr in attributes] == [loyalty_customer_attribute.slug]


def test_available_attributes_returns_unassigned_customer_attributes(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
    loyalty_customer_attribute,
    segment_customer_attribute,
    hidden_customer_attribute,
    size_page_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    customer_type.customer_attributes.add(loyalty_customer_attribute)
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TYPE_AVAILABLE_ATTRIBUTES_QUERY, variables
    )

    # then
    content = get_graphql_content(response)
    available = content["data"]["customerType"]["availableAttributes"]
    assert available["totalCount"] == 2
    assert {edge["node"]["slug"] for edge in available["edges"]} == {
        segment_customer_attribute.slug,
        hidden_customer_attribute.slug,
    }


def test_available_attributes_by_staff_without_permission(
    staff_api_client, customer_type, segment_customer_attribute
):
    # given
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TYPE_AVAILABLE_ATTRIBUTES_QUERY, variables
    )

    # then
    assert_no_permission(response)


def test_available_attributes_search(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
    loyalty_customer_attribute,
    segment_customer_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    variables = {
        "id": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "search": segment_customer_attribute.name,
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TYPE_AVAILABLE_ATTRIBUTES_QUERY, variables
    )

    # then
    content = get_graphql_content(response)
    available = content["data"]["customerType"]["availableAttributes"]
    assert available["totalCount"] == 1
    assert available["edges"][0]["node"]["slug"] == segment_customer_attribute.slug


def test_available_attributes_where_slug(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
    loyalty_customer_attribute,
    segment_customer_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    variables = {
        "id": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "where": {"slug": {"eq": loyalty_customer_attribute.slug}},
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TYPE_AVAILABLE_ATTRIBUTES_QUERY, variables
    )

    # then
    content = get_graphql_content(response)
    available = content["data"]["customerType"]["availableAttributes"]
    assert available["totalCount"] == 1
    assert available["edges"][0]["node"]["slug"] == loyalty_customer_attribute.slug
