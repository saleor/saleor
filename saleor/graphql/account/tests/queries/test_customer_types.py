import graphene

from ....core.enums import OrderDirection
from ....tests.utils import assert_no_permission, get_graphql_content
from ...sorters import CustomerTypeSortField

CUSTOMER_TYPE_QUERY = """
    query CustomerType($id: ID!) {
        customerType(id: $id) {
            id
            name
            slug
            isDefault
        }
    }
"""

CUSTOMER_TYPES_QUERY = """
    query CustomerTypes(
        $where: CustomerTypeWhereInput,
        $search: String,
        $sortBy: CustomerTypeSortingInput
    ) {
        customerTypes(first: 10, where: $where, search: $search, sortBy: $sortBy) {
            edges {
                node {
                    id
                    name
                    slug
                    isDefault
                }
            }
            totalCount
        }
    }
"""


def test_customer_type_query_by_staff_without_permissions(
    staff_api_client, customer_type
):
    # given
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    customer_type_data = content["data"]["customerType"]
    assert customer_type_data["name"] == customer_type.name
    assert customer_type_data["slug"] == customer_type.slug
    assert customer_type_data["isDefault"] == customer_type.is_default


def test_customer_type_query_by_app(app_api_client, customer_type):
    # given
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = app_api_client.post_graphql(CUSTOMER_TYPE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    customer_type_data = content["data"]["customerType"]
    assert customer_type_data["slug"] == customer_type.slug


def test_customer_type_query_by_customer_no_permission(user_api_client, customer_type):
    # given
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = user_api_client.post_graphql(CUSTOMER_TYPE_QUERY, variables)

    # then
    assert_no_permission(response)


def test_customer_type_query_by_anonymous_no_permission(api_client, customer_type):
    # given
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = api_client.post_graphql(CUSTOMER_TYPE_QUERY, variables)

    # then
    assert_no_permission(response)


def test_customer_types_query_by_staff(
    staff_api_client, customer_type, default_customer_type
):
    # given

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPES_QUERY, {})

    # then
    content = get_graphql_content(response)
    customer_types_data = content["data"]["customerTypes"]
    assert customer_types_data["totalCount"] == 2
    slugs = {edge["node"]["slug"] for edge in customer_types_data["edges"]}
    assert slugs == {customer_type.slug, default_customer_type.slug}


def test_customer_types_query_by_customer_no_permission(user_api_client, customer_type):
    # when
    response = user_api_client.post_graphql(CUSTOMER_TYPES_QUERY, {})

    # then
    assert_no_permission(response)


def test_customer_types_query_search(
    staff_api_client, customer_type, default_customer_type
):
    # given
    variables = {"search": customer_type.name}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPES_QUERY, variables)

    # then
    content = get_graphql_content(response)
    customer_types_data = content["data"]["customerTypes"]
    assert customer_types_data["totalCount"] == 1
    assert customer_types_data["edges"][0]["node"]["slug"] == customer_type.slug


def test_customer_types_query_where_slug_one_of(
    staff_api_client, customer_type, default_customer_type
):
    # given
    variables = {"where": {"slug": {"oneOf": [default_customer_type.slug]}}}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPES_QUERY, variables)

    # then
    content = get_graphql_content(response)
    customer_types_data = content["data"]["customerTypes"]
    assert customer_types_data["totalCount"] == 1
    assert customer_types_data["edges"][0]["node"]["slug"] == default_customer_type.slug


def test_customer_types_query_where_ids(
    staff_api_client, customer_type, default_customer_type
):
    # given
    customer_type_id = graphene.Node.to_global_id("CustomerType", customer_type.pk)
    variables = {"where": {"ids": [customer_type_id]}}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPES_QUERY, variables)

    # then
    content = get_graphql_content(response)
    customer_types_data = content["data"]["customerTypes"]
    assert customer_types_data["totalCount"] == 1
    assert customer_types_data["edges"][0]["node"]["id"] == customer_type_id


def test_customer_types_query_where_is_default(
    staff_api_client, customer_type, default_customer_type
):
    # given
    variables = {"where": {"isDefault": True}}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPES_QUERY, variables)

    # then
    content = get_graphql_content(response)
    customer_types_data = content["data"]["customerTypes"]
    assert customer_types_data["totalCount"] == 1
    assert customer_types_data["edges"][0]["node"]["slug"] == default_customer_type.slug


def test_customer_types_query_sort_by_name_desc(
    staff_api_client, customer_type, default_customer_type
):
    # given
    variables = {
        "sortBy": {
            "field": CustomerTypeSortField.NAME.name,
            "direction": OrderDirection.DESC.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPES_QUERY, variables)

    # then
    content = get_graphql_content(response)
    customer_types_data = content["data"]["customerTypes"]
    names = [edge["node"]["name"] for edge in customer_types_data["edges"]]
    assert names == sorted(
        [customer_type.name, default_customer_type.name], reverse=True
    )
