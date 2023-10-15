import graphene

from ....tests.utils import assert_no_permission, get_graphql_content
from .utils import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE

QUERY_PAGE_TYPE_PUBLIC_META = """
    query pageTypeMeta($id: ID!){
        pageType(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_page_type_as_anonymous_user(api_client, page_type):
    # given
    page_type.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    page_type.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = api_client.post_graphql(QUERY_PAGE_TYPE_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["pageType"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_page_type_as_customer(user_api_client, page_type):
    # given
    page_type.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    page_type.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_PAGE_TYPE_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["pageType"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_page_type_as_staff(
    staff_api_client, page_type, permission_manage_products
):
    # given
    page_type.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    page_type.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGE_TYPE_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["pageType"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_page_type_as_app(
    app_api_client, page_type, permission_manage_products
):
    # given
    page_type.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    page_type.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_PAGE_TYPE_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["pageType"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_PAGE_TYPE_PRIVATE_META = """
    query pageTypeMeta($id: ID!){
        pageType(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_page_type_as_anonymous_user(api_client, page_type):
    # given
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = api_client.post_graphql(QUERY_PAGE_TYPE_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_page_type_as_customer(user_api_client, page_type):
    # given
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_PAGE_TYPE_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_page_type_as_staff(
    staff_api_client, page_type, permission_manage_page_types_and_attributes
):
    # given
    page_type.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    page_type.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGE_TYPE_PRIVATE_META,
        variables,
        [permission_manage_page_types_and_attributes],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["pageType"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_page_type_as_app(
    app_api_client, page_type, permission_manage_page_types_and_attributes
):
    # given
    page_type.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    page_type.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_PAGE_TYPE_PRIVATE_META,
        variables,
        [permission_manage_page_types_and_attributes],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["pageType"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE
