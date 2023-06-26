import graphene

from ....tests.utils import assert_no_permission, get_graphql_content
from .utils import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE

QUERY_ATTRIBUTE_PUBLIC_META = """
    query attributeMeta($id: ID!){
        attribute(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_attribute_as_anonymous_user(api_client, color_attribute):
    # given
    color_attribute.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    color_attribute.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = api_client.post_graphql(QUERY_ATTRIBUTE_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["attribute"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_attribute_as_customer(user_api_client, color_attribute):
    # given
    color_attribute.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    color_attribute.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_ATTRIBUTE_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["attribute"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_attribute_as_staff(
    staff_api_client, color_attribute, permission_manage_products
):
    # given
    color_attribute.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    color_attribute.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ATTRIBUTE_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["attribute"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_attribute_as_app(
    app_api_client, color_attribute, permission_manage_products
):
    # given
    color_attribute.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    color_attribute.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_ATTRIBUTE_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["attribute"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_ATTRIBUTE_PRIVATE_META = """
    query attributeMeta($id: ID!){
        attribute(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_attribute_as_anonymous_user(
    api_client, color_attribute
):
    # given
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = api_client.post_graphql(QUERY_ATTRIBUTE_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_attribute_as_customer(user_api_client, color_attribute):
    # given
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_ATTRIBUTE_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_attribute_as_staff(
    staff_api_client, color_attribute, permission_manage_product_types_and_attributes
):
    # given
    color_attribute.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    color_attribute.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ATTRIBUTE_PRIVATE_META,
        variables,
        [permission_manage_product_types_and_attributes],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["attribute"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_attribute_as_app(
    app_api_client, color_attribute, permission_manage_product_types_and_attributes
):
    # given
    color_attribute.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    color_attribute.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_ATTRIBUTE_PRIVATE_META,
        variables,
        [permission_manage_product_types_and_attributes],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["attribute"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE
