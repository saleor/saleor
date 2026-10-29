import graphene

from ....tests.utils import assert_no_permission, get_graphql_content
from .utils import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE

QUERY_CUSTOMER_TYPE_PUBLIC_META = """
    query customerTypeMeta($id: ID!){
        customerType(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_customer_type_as_staff(staff_api_client, customer_type):
    # given
    customer_type.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    customer_type.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMER_TYPE_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["customerType"]["metadata"]
    assert len(metadata) == 1
    assert metadata[0]["key"] == PUBLIC_KEY
    assert metadata[0]["value"] == PUBLIC_VALUE


def test_query_public_meta_for_customer_type_as_app(app_api_client, customer_type):
    # given
    customer_type.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    customer_type.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = app_api_client.post_graphql(QUERY_CUSTOMER_TYPE_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["customerType"]["metadata"]
    assert len(metadata) == 1
    assert metadata[0]["key"] == PUBLIC_KEY
    assert metadata[0]["value"] == PUBLIC_VALUE


QUERY_CUSTOMER_TYPE_PRIVATE_META = """
    query customerTypeMeta($id: ID!){
        customerType(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_customer_type_as_staff(
    staff_api_client, customer_type, permission_manage_customer_types_and_attributes
):
    # given
    customer_type.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    customer_type.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CUSTOMER_TYPE_PRIVATE_META,
        variables,
        [permission_manage_customer_types_and_attributes],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["customerType"]["privateMetadata"]
    assert len(metadata) == 1
    assert metadata[0]["key"] == PRIVATE_KEY
    assert metadata[0]["value"] == PRIVATE_VALUE


def test_query_private_meta_for_customer_type_as_app(
    app_api_client, customer_type, permission_manage_customer_types_and_attributes
):
    # given
    customer_type.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    customer_type.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_CUSTOMER_TYPE_PRIVATE_META,
        variables,
        [permission_manage_customer_types_and_attributes],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["customerType"]["privateMetadata"]
    assert len(metadata) == 1
    assert metadata[0]["key"] == PRIVATE_KEY
    assert metadata[0]["value"] == PRIVATE_VALUE


def test_query_private_meta_for_customer_type_as_staff_without_permission(
    staff_api_client, customer_type
):
    # given
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CUSTOMER_TYPE_PRIVATE_META, variables
    )

    # then
    assert_no_permission(response)


def test_query_private_meta_for_customer_type_as_app_without_permission(
    app_api_client, customer_type
):
    # given
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = app_api_client.post_graphql(QUERY_CUSTOMER_TYPE_PRIVATE_META, variables)

    # then
    assert_no_permission(response)
