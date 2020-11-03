import graphene

from ...tests.utils import assert_no_permission, get_graphql_content

PAGE_TYPE_QUERY = """
    query PageType($id: ID!, $filters: AttributeFilterInput) {
        pageType(id: $id) {
            id
            name
            slug
            hasPages
            attributes {
                slug
            }
            availableAttributes(first: 10, filter: $filters) {
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
