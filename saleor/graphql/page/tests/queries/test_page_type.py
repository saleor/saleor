import graphene

from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

PAGE_TYPE_QUERY = """
    query PageType(
        $id: ID!, $filters: AttributeFilterInput, $where: AttributeWhereInput
    ) {
        pageType(id: $id) {
            id
            name
            slug
            hasPages
            attributes {
                slug
            }
            availableAttributes(first: 10, filter: $filters, where: $where) {
                edges {
                    node {
                        slug
                    }
                }
            }
        }
    }
"""


def test_page_type_query_by_staff(
    staff_api_client,
    page_type,
    author_page_attribute,
    permission_manage_pages,
    color_attribute,
    page,
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_pages)

    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = staff_api_client.post_graphql(PAGE_TYPE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    page_type_data = content["data"]["pageType"]

    assert page_type_data["slug"] == page_type.slug
    assert page_type_data["name"] == page_type.name
    assert {attr["slug"] for attr in page_type_data["attributes"]} == {
        attr.slug for attr in page_type.page_attributes.all()
    }
    assert page_type_data["hasPages"] is True
    available_attributes = page_type_data["availableAttributes"]["edges"]
    assert len(available_attributes) == 1
    assert available_attributes[0]["node"]["slug"] == author_page_attribute.slug


def test_page_type_query_by_staff_no_perm(
    staff_api_client, page_type, author_page_attribute
):
    # given
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = staff_api_client.post_graphql(PAGE_TYPE_QUERY, variables)

    # then
    assert_no_permission(response)


def test_page_type_query_by_app(
    app_api_client,
    page_type,
    author_page_attribute,
    permission_manage_pages,
    color_attribute,
):
    # given
    staff_user = app_api_client.app
    staff_user.permissions.add(permission_manage_pages)

    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = app_api_client.post_graphql(PAGE_TYPE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    page_type_data = content["data"]["pageType"]

    assert page_type_data["slug"] == page_type.slug
    assert page_type_data["name"] == page_type.name
    assert {attr["slug"] for attr in page_type_data["attributes"]} == {
        attr.slug for attr in page_type.page_attributes.all()
    }
    available_attributes = page_type_data["availableAttributes"]["edges"]
    assert len(available_attributes) == 1
    assert available_attributes[0]["node"]["slug"] == author_page_attribute.slug


def test_page_type_query_by_app_no_perm(
    app_api_client,
    page_type,
    author_page_attribute,
    permission_manage_page_types_and_attributes,
):
    # given
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = app_api_client.post_graphql(PAGE_TYPE_QUERY, variables)

    # then
    assert_no_permission(response)


def test_staff_query_page_type_by_invalid_id(staff_api_client, page_type):
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(PAGE_TYPE_QUERY, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["pageType"] is None


def test_staff_query_page_type_with_invalid_object_type(staff_api_client, page_type):
    variables = {"id": graphene.Node.to_global_id("Order", page_type.pk)}
    response = staff_api_client.post_graphql(PAGE_TYPE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["pageType"] is None


def test_page_type_query_filter_unassigned_attributes(
    staff_api_client,
    page_type,
    permission_manage_pages,
    page_type_attribute_list,
    color_attribute,
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_pages)

    expected_attribute = page_type_attribute_list[0]

    variables = {
        "id": graphene.Node.to_global_id("PageType", page_type.pk),
        "filters": {"search": expected_attribute.name},
    }

    # when
    response = staff_api_client.post_graphql(PAGE_TYPE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    page_type_data = content["data"]["pageType"]

    assert page_type_data["slug"] == page_type.slug
    assert {attr["slug"] for attr in page_type_data["attributes"]} == {
        attr.slug for attr in page_type.page_attributes.all()
    }
    available_attributes = page_type_data["availableAttributes"]["edges"]
    assert len(available_attributes) == 1
    assert available_attributes[0]["node"]["slug"] == expected_attribute.slug


def test_page_type_query_where_filter_unassigned_attributes(
    staff_api_client,
    page_type,
    permission_manage_pages,
    page_type_attribute_list,
    color_attribute,
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_pages)

    expected_attribute = page_type_attribute_list[0]

    variables = {
        "id": graphene.Node.to_global_id("PageType", page_type.pk),
        "where": {"name": {"eq": expected_attribute.name}},
    }

    # when
    response = staff_api_client.post_graphql(PAGE_TYPE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    page_type_data = content["data"]["pageType"]

    assert page_type_data["slug"] == page_type.slug
    assert {attr["slug"] for attr in page_type_data["attributes"]} == {
        attr.slug for attr in page_type.page_attributes.all()
    }
    available_attributes = page_type_data["availableAttributes"]["edges"]
    assert len(available_attributes) == 1
    assert available_attributes[0]["node"]["slug"] == expected_attribute.slug


def test_page_type_query_no_pages(
    staff_api_client,
    page_type,
    author_page_attribute,
    permission_manage_pages,
    color_attribute,
):
    # given
    staff_user = staff_api_client.user
    staff_user.user_permissions.add(permission_manage_pages)

    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = staff_api_client.post_graphql(PAGE_TYPE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    page_type_data = content["data"]["pageType"]

    assert page_type_data["slug"] == page_type.slug
    assert page_type_data["name"] == page_type.name
    assert {attr["slug"] for attr in page_type_data["attributes"]} == {
        attr.slug for attr in page_type.page_attributes.all()
    }
    assert page_type_data["hasPages"] is False
    available_attributes = page_type_data["availableAttributes"]["edges"]
    assert len(available_attributes) == 1
    assert available_attributes[0]["node"]["slug"] == author_page_attribute.slug


def test_query_page_types_for_federation(api_client, page_type):
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)
    variables = {
        "representations": [
            {
                "__typename": "PageType",
                "id": page_type_id,
            },
        ],
    }
    query = """
      query GetPageTypeInFederation($representations: [_Any]) {
        _entities(representations: $representations) {
          __typename
          ... on PageType {
            id
            name
          }
        }
      }
    """

    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "PageType",
            "id": page_type_id,
            "name": page_type.name,
        }
    ]
