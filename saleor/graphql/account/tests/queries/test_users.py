import graphene

from .....order import OrderStatus
from .....order.models import Order
from ....tests.utils import assert_no_permission, get_graphql_content


def test_query_customers(staff_api_client, user_api_client, permission_manage_users):
    query = """
    query Users {
        customers(first: 20) {
            totalCount
            edges {
                node {
                    isStaff
                }
            }
        }
    }
    """
    variables = {}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    users = content["data"]["customers"]["edges"]
    assert users
    assert all(not user["node"]["isStaff"] for user in users)

    # check permissions
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_query_staff(
    staff_api_client, user_api_client, staff_user, admin_user, permission_manage_staff
):
    query = """
    {
        staffUsers(first: 20) {
            edges {
                node {
                    email
                    isStaff
                }
            }
        }
    }
    """
    variables = {}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffUsers"]["edges"]
    assert len(data) == 2
    staff_emails = [user["node"]["email"] for user in data]
    assert sorted(staff_emails) == [admin_user.email, staff_user.email]
    assert all(user["node"]["isStaff"] for user in data)

    # check permissions
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


USER_QUERY = """
    query User($id: ID $email: String, $externalReference: String) {
        user(id: $id, email: $email, externalReference: $externalReference) {
            id
            email
            externalReference
        }
    }
"""


def test_who_can_see_user(
    staff_user, customer_user, staff_api_client, permission_manage_users
):
    query = """
    query Users {
        customers {
            totalCount
        }
    }
    """

    # Random person (even staff) can't see users data without permissions
    ID = graphene.Node.to_global_id("User", customer_user.id)
    variables = {"id": ID}
    response = staff_api_client.post_graphql(USER_QUERY, variables)
    assert_no_permission(response)

    response = staff_api_client.post_graphql(query)
    assert_no_permission(response)

    # Add permission and ensure staff can see user(s)
    staff_user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(USER_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["user"]["email"] == customer_user.email

    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    assert content["data"]["customers"]["totalCount"] == 1


USER_ORDERS_WHERE_QUERY = """
    query User($id: ID!, $where: CustomerOrderWhereInput) {
        user(id: $id) {
            orderswithFilter: orders(first: 10, where: $where) {
                totalCount
                edges {
                    node {
                        id
                        number
                    }
                }
            }
            orderNoFilter: orders(first: 10) {
                totalCount
                edges {
                    node {
                        id
                        number
                    }
                }
            }
        }
    }
"""


def test_user_orders_where_filter_and_unfiltered_in_single_query(
    staff_api_client,
    customer_user,
    order_list,
    permission_group_manage_orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_list[0].user = customer_user
    order_list[0].status = OrderStatus.UNCONFIRMED
    order_list[1].user = customer_user
    order_list[1].status = OrderStatus.UNFULFILLED
    order_list[2].user = customer_user
    order_list[2].status = OrderStatus.UNFULFILLED
    Order.objects.bulk_update(order_list, ["user", "status"])

    user_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {
        "id": user_id,
        "where": {"status": {"eq": OrderStatus.UNCONFIRMED.upper()}},
    }

    # when
    response = staff_api_client.post_graphql(USER_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    user_data = content["data"]["user"]

    filtered_orders = user_data["orderswithFilter"]
    assert filtered_orders["totalCount"] == 1
    assert filtered_orders["edges"][0]["node"]["id"] == graphene.Node.to_global_id(
        "Order", order_list[0].pk
    )

    unfiltered_orders = user_data["orderNoFilter"]
    assert unfiltered_orders["totalCount"] == 3
    returned_ids = {edge["node"]["id"] for edge in unfiltered_orders["edges"]}
    assert returned_ids == {
        graphene.Node.to_global_id("Order", order.pk) for order in order_list
    }
