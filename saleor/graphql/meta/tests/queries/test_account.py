import graphene

from ....tests.utils import assert_no_permission, get_graphql_content
from .utils import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE

QUERY_USER_PUBLIC_META = """
    query userMeta($id: ID!){
        user(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_customer_as_staff(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    customer_user.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_USER_PUBLIC_META, variables, [permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["user"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_customer_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    customer_user.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_USER_PUBLIC_META, variables, [permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["user"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_staff_as_other_staff(
    staff_api_client, permission_manage_staff, admin_user
):
    # given
    admin_user.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    admin_user.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("User", admin_user.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_USER_PUBLIC_META, variables, [permission_manage_staff]
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["user"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_USER_PRIVATE_META = """
    query userMeta($id: ID!){
        user(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_customer_as_staff(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    customer_user.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_USER_PRIVATE_META, variables, [permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["user"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_customer_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    customer_user.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_USER_PRIVATE_META, variables, [permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["user"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_staff_as_other_staff(
    staff_api_client, permission_manage_staff, admin_user
):
    # given
    admin_user.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    admin_user.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("User", admin_user.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_USER_PRIVATE_META, variables, [permission_manage_staff]
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["user"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_SELF_PUBLIC_META = """
    {
        me{
            metadata{
                key
                value
            }
            metafields(keys: ["INVALID", "key"])
            keyFieldValue: metafield(key: "key")
        }
    }
"""


def test_query_public_meta_for_me_as_customer(user_api_client):
    # given
    me = user_api_client.user
    me.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    me.save(update_fields=["metadata"])

    # when
    response = user_api_client.post_graphql(QUERY_SELF_PUBLIC_META)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["me"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE
    metafields = content["data"]["me"]["metafields"]
    assert metafields[PUBLIC_KEY] == PUBLIC_VALUE
    field_value = content["data"]["me"]["keyFieldValue"]
    assert field_value == PUBLIC_VALUE


def test_query_public_meta_for_me_as_staff(staff_api_client):
    # given
    me = staff_api_client.user
    me.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    me.save(update_fields=["metadata"])

    # when
    response = staff_api_client.post_graphql(QUERY_SELF_PUBLIC_META)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["me"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE
    metafields = content["data"]["me"]["metafields"]
    assert metafields[PUBLIC_KEY] == PUBLIC_VALUE
    field_value = content["data"]["me"]["keyFieldValue"]
    assert field_value == PUBLIC_VALUE


QUERY_SELF_PRIVATE_META = """
    {
        me{
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_me_as_customer(user_api_client):
    # given

    # when
    response = user_api_client.post_graphql(QUERY_SELF_PRIVATE_META)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_me_as_staff_with_manage_customer(
    staff_api_client, permission_manage_users
):
    # given

    # when
    response = staff_api_client.post_graphql(
        QUERY_SELF_PRIVATE_META, None, [permission_manage_users]
    )

    # then
    assert_no_permission(response)


def test_query_private_meta_for_me_as_staff_with_manage_staff(
    staff_api_client, permission_manage_staff
):
    # given
    me = staff_api_client.user
    me.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    me.save(update_fields=["private_metadata"])

    # when
    response = staff_api_client.post_graphql(
        QUERY_SELF_PRIVATE_META, None, [permission_manage_staff]
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["me"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE
