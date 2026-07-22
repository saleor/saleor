import graphene

from ....tests.utils import assert_no_permission, get_graphql_content

USER_CUSTOMER_TYPE_QUERY = """
    query User($id: ID!) {
        user(id: $id) {
            id
            customerType {
                id
                name
                slug
                isDefault
            }
        }
    }
"""

ME_CUSTOMER_TYPE_QUERY = """
    query Me {
        me {
            id
            customerType {
                id
                name
                slug
            }
        }
    }
"""


def test_customer_type_visible_to_staff_with_manage_users(
    staff_api_client, permission_manage_users, customer_user, customer_type
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_users)
    customer_user.customer_type = customer_type
    customer_user.save(update_fields=["customer_type"])
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = staff_api_client.post_graphql(USER_CUSTOMER_TYPE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    customer_type_data = content["data"]["user"]["customerType"]
    assert customer_type_data["name"] == customer_type.name
    assert customer_type_data["slug"] == customer_type.slug
    assert customer_type_data["isDefault"] == customer_type.is_default


def test_customer_type_visible_to_owner(user_api_client, customer_user, customer_type):
    # given
    customer_user.customer_type = customer_type
    customer_user.save(update_fields=["customer_type"])

    # when
    response = user_api_client.post_graphql(ME_CUSTOMER_TYPE_QUERY)

    # then
    content = get_graphql_content(response)
    customer_type_data = content["data"]["me"]["customerType"]
    assert customer_type_data["slug"] == customer_type.slug


def test_customer_type_not_visible_to_staff_without_permission(
    staff_api_client, permission_manage_orders, customer_user, customer_type
):
    # given the customers query is reachable with MANAGE_ORDERS, but the
    # customerType field requires MANAGE_USERS or ownership
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    customer_user.customer_type = customer_type
    customer_user.save(update_fields=["customer_type"])
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = staff_api_client.post_graphql(USER_CUSTOMER_TYPE_QUERY, variables)

    # then
    assert_no_permission(response)


def test_customer_type_falls_back_to_default_when_not_assigned(
    user_api_client, customer_user, default_customer_type
):
    # given a user created before the backfill finished
    assert customer_user.customer_type_id is None

    # when
    response = user_api_client.post_graphql(ME_CUSTOMER_TYPE_QUERY)

    # then
    content = get_graphql_content(response)
    customer_type_data = content["data"]["me"]["customerType"]
    assert customer_type_data["slug"] == default_customer_type.slug
