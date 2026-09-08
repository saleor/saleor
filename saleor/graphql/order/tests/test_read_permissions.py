"""READ_ORDERS permission model (order domain).

Seam under test: the GraphQL API (execute query/mutation as a principal, observe response).

Invariants:
  A. Parity        - READ_ORDERS sees the same reads as MANAGE_ORDERS
  B. No write leak - READ_ORDERS is rejected by MANAGE_ORDERS mutations
  C. Regression    - MANAGE_ORDERS behavior unchanged; no-perms still denied
  E. Metadata      - READ_ORDERS unlocks private metadata reads (dynamic perm resolution)
  G. Grant-scope   - MANAGE_ORDERS covers granting its READ_ORDERS twin (appCreate)

READ_ORDERS parity is enforced through the `orders` list field gate, the
`Order.user` / `Order.transactions` read gates (the manual owner/permission
checks widened via expand_read_permissions), and private-metadata resolution.
"""

import graphene

from ....order import OrderStatus
from ....permission.enums import OrderPermissions
from ...core.enums import PermissionEnum
from ...tests.utils import assert_no_permission, get_graphql_content

ORDER_USER_QUERY = """
    query ($id: ID!) {
        order(id: $id) {
            id
            user { email }
        }
    }
"""

ORDER_TRANSACTIONS_QUERY = """
    query ($id: ID!) {
        order(id: $id) {
            id
            transactions { id }
        }
    }
"""

ORDER_PRIVATE_META_QUERY = """
    query ($id: ID!) {
        order(id: $id) {
            id
            privateMetadata { key value }
        }
    }
"""

ORDERS_LIST_QUERY = """
    query {
        orders(first: 20) {
            edges { node { id } }
        }
    }
"""

ORDER_CANCEL_MUTATION = """
    mutation ($id: ID!) {
        orderCancel(id: $id) {
            order { id status }
            errors { field code }
        }
    }
"""

APP_CREATE_MUTATION = """
    mutation AppCreate($name: String, $permissions: [PermissionEnum!]) {
        appCreate(input: {name: $name, permissions: $permissions}) {
            app { permissions { code } }
            errors { field code permissions }
        }
    }
"""


# --------------------------------------------------------------------------- #
# A. Parity - READ_ORDERS sees the same reads as MANAGE_ORDERS
# --------------------------------------------------------------------------- #


def test_read_orders_reads_order_user(staff_api_client, order, permission_read_orders):
    # given a staff user holding only READ_ORDERS
    staff_api_client.user.user_permissions.add(permission_read_orders)
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when reading the order's (owner-gated) user field
    response = staff_api_client.post_graphql(ORDER_USER_QUERY, variables)

    # then the customer is returned (parity with MANAGE_ORDERS)
    content = get_graphql_content(response)
    assert content["data"]["order"]["user"]["email"] == order.user.email


def test_read_orders_reads_order_transactions(
    staff_api_client, order, transaction_item, permission_read_orders
):
    # given a staff user holding only READ_ORDERS and an order with a transaction
    staff_api_client.user.user_permissions.add(permission_read_orders)
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}
    expected_id = graphene.Node.to_global_id("TransactionItem", transaction_item.token)

    # when reading the permission-gated transactions field
    response = staff_api_client.post_graphql(ORDER_TRANSACTIONS_QUERY, variables)

    # then the transaction is returned (parity with MANAGE_ORDERS/HANDLE_PAYMENTS)
    content = get_graphql_content(response)
    transactions = content["data"]["order"]["transactions"]
    assert [txn["id"] for txn in transactions] == [expected_id]


# --------------------------------------------------------------------------- #
# B. No write leak - READ_ORDERS is rejected by MANAGE_ORDERS mutations
# --------------------------------------------------------------------------- #


def test_read_orders_cannot_cancel_order(
    staff_api_client, order_unconfirmed, permission_read_orders
):
    # given a staff user holding only READ_ORDERS
    order = order_unconfirmed
    assert order.status != OrderStatus.CANCELED
    staff_api_client.user.user_permissions.add(permission_read_orders)
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when attempting a MANAGE_ORDERS mutation
    response = staff_api_client.post_graphql(ORDER_CANCEL_MUTATION, variables)

    # then it is denied and the order is unchanged
    assert_no_permission(response)
    order.refresh_from_db(fields=["status"])
    assert order.status != OrderStatus.CANCELED


# --------------------------------------------------------------------------- #
# C. Regression - MANAGE_ORDERS unchanged; no-perms denied
# --------------------------------------------------------------------------- #


def test_manage_orders_still_reads_order_user(
    staff_api_client, order, permission_manage_orders
):
    # given a staff user holding MANAGE_ORDERS (baseline)
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when reading the order's user field
    response = staff_api_client.post_graphql(ORDER_USER_QUERY, variables)

    # then the customer is returned (no regression)
    content = get_graphql_content(response)
    assert content["data"]["order"]["user"]["email"] == order.user.email


def test_no_perms_staff_cannot_read_order_user(staff_api_client, order):
    # given a staff user with no relevant permissions
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when reading the owner-gated user field
    response = staff_api_client.post_graphql(ORDER_USER_QUERY, variables)

    # then it is denied - adding the READ twin did not widen unprivileged access
    assert_no_permission(response)


# --------------------------------------------------------------------------- #
# E. Metadata - READ_ORDERS unlocks private metadata reads
# --------------------------------------------------------------------------- #


def test_read_orders_reads_order_private_metadata(
    staff_api_client, order, permission_read_orders
):
    # given an order with private metadata and a READ_ORDERS-only staff user
    order.store_value_in_private_metadata({"secret": "value"})
    order.save(update_fields=["private_metadata"])
    staff_api_client.user.user_permissions.add(permission_read_orders)
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when reading the order's private metadata
    response = staff_api_client.post_graphql(ORDER_PRIVATE_META_QUERY, variables)

    # then the private metadata is returned
    content = get_graphql_content(response)
    metadata = {
        item["key"]: item["value"]
        for item in content["data"]["order"]["privateMetadata"]
    }
    assert metadata["secret"] == "value"


# --------------------------------------------------------------------------- #
# G. Grant-scope - MANAGE_ORDERS covers granting its READ_ORDERS twin
# --------------------------------------------------------------------------- #


def test_app_create_read_orders_inferred_from_manage_orders(
    staff_api_client, permission_manage_apps, permission_manage_orders
):
    # given a staff user with MANAGE_APPS + MANAGE_ORDERS and NO READ_ORDERS
    staff_api_client.user.user_permissions.add(
        permission_manage_apps, permission_manage_orders
    )
    variables = {
        "name": "read app",
        "permissions": [PermissionEnum.READ_ORDERS.name],
    }

    # when creating an app that should hold READ_ORDERS
    response = staff_api_client.post_graphql(APP_CREATE_MUTATION, variables)

    # then the app is created holding read_orders - inferred from MANAGE_ORDERS
    content = get_graphql_content(response)
    data = content["data"]["appCreate"]
    assert data["errors"] == []
    codes = {perm["code"] for perm in data["app"]["permissions"]}
    assert codes == {PermissionEnum.READ_ORDERS.name}


def test_app_with_read_orders_can_list_orders(
    app_api_client, order, permission_read_orders
):
    # given an app holding READ_ORDERS
    app_api_client.app.permissions.add(permission_read_orders)

    # when listing orders
    response = app_api_client.post_graphql(
        ORDERS_LIST_QUERY, check_no_permissions=False
    )

    # then the order is listed (apps are a primary target audience)
    content = get_graphql_content(response)
    ids = {edge["node"]["id"] for edge in content["data"]["orders"]["edges"]}
    assert graphene.Node.to_global_id("Order", order.pk) in ids


def test_registry_maps_order_twin():
    # given the registry entries
    from ....permission.read_permissions import MANAGE_TO_READ_PERMISSION_MAP

    # then MANAGE_ORDERS maps to its READ twin
    assert (
        MANAGE_TO_READ_PERMISSION_MAP[OrderPermissions.MANAGE_ORDERS]
        == OrderPermissions.READ_ORDERS
    )
