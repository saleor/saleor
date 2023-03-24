from decimal import Decimal

from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import OrderGrantRefundCreateErrorCode

ORDER_GRANT_REFUND_CREATE = """
mutation OrderGrantRefundCreate(
    $id: ID!, $input: OrderGrantRefundCreateInput!
){
  orderGrantRefundCreate(id: $id, input:$input){
    grantedRefund{
      id
      createdAt
      updatedAt
      amount{
        amount
      }
      reason
      user{
        id
      }
      app{
        id
      }
    }
    order{
      id
      grantedRefunds{
        id
        amount{
          amount
        }
        createdAt
        updatedAt
        reason
        app{
          id
        }
        user{
          id
        }
      }
    }
    errors{
      field
      code
    }
  }
}
"""


def test_grant_refund_by_user(staff_api_client, permission_manage_orders, order):
    # given
    order_id = to_global_id_or_none(order)
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    amount = Decimal("10.00")
    reason = "Granted refund reason."
    variables = {
        "id": order_id,
        "input": {"amount": amount, "reason": reason},
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then

    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert not errors

    assert order_id == data["order"]["id"]
    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_from_db = order.granted_refunds.first()
    granted_refund_assigned_to_order = data["order"]["grantedRefunds"][0]
    assert granted_refund_assigned_to_order == data["grantedRefund"]
    assert (
        granted_refund_assigned_to_order["amount"]["amount"]
        == granted_refund_from_db.amount_value
        == amount
    )
    assert (
        granted_refund_assigned_to_order["reason"]
        == reason
        == granted_refund_from_db.reason
    )
    assert (
        granted_refund_assigned_to_order["user"]["id"]
        == to_global_id_or_none(staff_api_client.user)
        == to_global_id_or_none(granted_refund_from_db.user)
    )
    assert not granted_refund_assigned_to_order["app"]


def test_grant_refund_by_app(app_api_client, permission_manage_orders, order):
    # given
    order_id = to_global_id_or_none(order)
    app_api_client.app.permissions.set([permission_manage_orders])
    amount = Decimal("10.00")
    reason = "Granted refund reason."
    variables = {
        "id": order_id,
        "input": {"amount": amount, "reason": reason},
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert not errors

    assert order_id == data["order"]["id"]
    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_from_db = order.granted_refunds.first()
    granted_refund = data["order"]["grantedRefunds"][0]
    assert granted_refund == data["grantedRefund"]
    assert (
        granted_refund["amount"]["amount"]
        == amount
        == granted_refund_from_db.amount_value
    )
    assert granted_refund["reason"] == reason == granted_refund_from_db.reason
    assert not granted_refund["user"]
    assert (
        granted_refund["app"]["id"]
        == to_global_id_or_none(app_api_client.app)
        == to_global_id_or_none(granted_refund_from_db.app)
    )


def test_grant_refund_by_app_missing_permission(app_api_client, order):
    # given
    order_id = to_global_id_or_none(order)
    amount = Decimal("10.00")
    reason = "Granted refund reason."
    variables = {
        "id": order_id,
        "input": {"amount": amount, "reason": reason},
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    assert_no_permission(response)


def test_grant_refund_by_user_missing_permission(staff_api_client, order):
    # given
    order_id = to_global_id_or_none(order)
    amount = Decimal("10.00")
    reason = "Granted refund reason."
    variables = {
        "id": order_id,
        "input": {"amount": amount, "reason": reason},
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    assert_no_permission(response)


def test_grant_refund_incorrect_order_id(staff_api_client, permission_manage_orders):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    amount = Decimal("10.00")
    reason = "Granted refund reason."
    variables = {
        "id": "wrong-id",
        "input": {"amount": amount, "reason": reason},
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then

    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == OrderGrantRefundCreateErrorCode.GRAPHQL_ERROR.name
