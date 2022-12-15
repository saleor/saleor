from decimal import Decimal

from ....core.utils import to_global_id_or_none
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ...enums import OrderGrantRefundUpdateErrorCode

ORDER_GRANT_REFUND_UPDATE = """
mutation OrderGrantRefundUpdate(
    $id: ID!, $input: OrderGrantRefundUpdateInput!
){
  orderGrantRefundUpdate(id: $id, input:$input) {
    grantedRefund {
      id
      createdAt
      updatedAt
      amount {
        amount
      }
      reason
      user {
        id
      }
      app {
        id
      }
    }
    order {
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
    errors {
      field
      code
    }
  }
}

"""


def test_grant_refund_update_by_user(
    staff_api_client, app, permission_manage_orders, order
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        app=app,
    )
    updated_at = granted_refund.updated_at
    granted_refund_id = to_global_id_or_none(granted_refund)
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    amount = Decimal("20.00")
    reason = "New reason"
    variables = {
        "id": granted_refund_id,
        "input": {"amount": amount, "reason": reason},
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]

    assert data["order"]["id"] == to_global_id_or_none(order)
    assert len(data["order"]["grantedRefunds"]) == 1

    granted_refund_assigned_to_order = data["order"]["grantedRefunds"][0]
    assert granted_refund_assigned_to_order == data["grantedRefund"]
    assert updated_at.isoformat() != data["grantedRefund"]["updatedAt"]
    granted_refund.refresh_from_db()
    assert granted_refund.updated_at.isoformat() == data["grantedRefund"]["updatedAt"]
    assert (
        granted_refund_assigned_to_order["amount"]["amount"]
        == granted_refund.amount_value
        == amount
    )
    assert granted_refund_assigned_to_order["reason"] == reason == granted_refund.reason
    assert granted_refund_assigned_to_order["app"]["id"] == to_global_id_or_none(
        granted_refund.app
    )


def test_grant_refund_update_only_amount_by_user(
    staff_api_client, app, permission_manage_orders, order
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        app=app,
    )
    granted_refund_id = to_global_id_or_none(granted_refund)
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    amount = Decimal("20.00")
    variables = {
        "id": granted_refund_id,
        "input": {"amount": amount},
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]

    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund.refresh_from_db()
    granted_refund_assigned_to_order = data["order"]["grantedRefunds"][0]
    assert granted_refund_assigned_to_order == data["grantedRefund"]
    assert (
        granted_refund_assigned_to_order["amount"]["amount"]
        == granted_refund.amount_value
        == amount
    )
    assert granted_refund.reason == current_reason


def test_grant_refund_update_only_reason_by_user(
    staff_api_client, app, permission_manage_orders, order
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        app=app,
    )
    granted_refund_id = to_global_id_or_none(granted_refund)
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    reason = "new reason"
    variables = {
        "id": granted_refund_id,
        "input": {"reason": reason},
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]

    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund.refresh_from_db()
    granted_refund_assigned_to_order = data["order"]["grantedRefunds"][0]
    assert granted_refund_assigned_to_order == data["grantedRefund"]
    assert granted_refund_assigned_to_order["reason"] == reason == granted_refund.reason
    assert granted_refund.amount_value == current_amount


def test_grant_refund_update_by_user_missing_permission(staff_api_client, app, order):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        app=app,
    )
    amount = Decimal("10.00")
    reason = "Granted refund reason."
    variables = {
        "id": to_global_id_or_none(granted_refund),
        "input": {"amount": amount, "reason": reason},
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    assert_no_permission(response)


def test_grant_refund_update_by_user_missing_input(
    staff_api_client, staff_user, order, permission_manage_orders
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        user=staff_user,
    )

    variables = {
        "id": to_global_id_or_none(granted_refund),
        "input": {},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    content = get_graphql_content_from_response(response)
    errors = content["data"]["orderGrantRefundUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderGrantRefundUpdateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "input"


def test_grant_refund_update_by_app(
    app_api_client, staff_user, permission_manage_orders, order, permission_manage_users
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        user=staff_user,
    )
    updated_at = granted_refund.updated_at
    granted_refund_id = to_global_id_or_none(granted_refund)
    app_api_client.app.permissions.set(
        [permission_manage_orders, permission_manage_users]
    )
    amount = Decimal("20.00")
    reason = "New reason"
    variables = {
        "id": granted_refund_id,
        "input": {"amount": amount, "reason": reason},
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]

    assert not data["errors"]

    assert data["order"]["id"] == to_global_id_or_none(order)
    assert len(data["order"]["grantedRefunds"]) == 1

    granted_refund_assigned_to_order = data["order"]["grantedRefunds"][0]
    assert granted_refund_assigned_to_order == data["grantedRefund"]
    assert updated_at.isoformat() != data["grantedRefund"]["updatedAt"]
    granted_refund.refresh_from_db()
    assert granted_refund.updated_at.isoformat() == data["grantedRefund"]["updatedAt"]
    assert (
        granted_refund_assigned_to_order["amount"]["amount"]
        == granted_refund.amount_value
        == amount
    )
    assert granted_refund_assigned_to_order["reason"] == reason == granted_refund.reason
    assert granted_refund_assigned_to_order["user"]["id"] == to_global_id_or_none(
        granted_refund.user
    )


def test_grant_refund_update_only_amount_by_app(
    app_api_client, staff_user, permission_manage_orders, order
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        user=staff_user,
    )
    granted_refund_id = to_global_id_or_none(granted_refund)
    app_api_client.app.permissions.set([permission_manage_orders])
    amount = Decimal("20.00")
    variables = {
        "id": granted_refund_id,
        "input": {"amount": amount},
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]

    granted_refund_assigned_to_order = data["order"]["grantedRefunds"][0]
    assert granted_refund_assigned_to_order == data["grantedRefund"]
    granted_refund.refresh_from_db()
    assert (
        granted_refund_assigned_to_order["amount"]["amount"]
        == granted_refund.amount_value
        == amount
    )
    assert (
        granted_refund_assigned_to_order["reason"]
        == current_reason
        == granted_refund.reason
    )


def test_grant_refund_update_only_reason_by_app(
    app_api_client, staff_user, permission_manage_orders, order
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        user=staff_user,
    )
    granted_refund_id = to_global_id_or_none(granted_refund)
    app_api_client.app.permissions.set([permission_manage_orders])

    reason = "new reason"
    variables = {
        "id": granted_refund_id,
        "input": {"reason": reason},
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]

    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund.refresh_from_db()
    granted_refund_assigned_to_order = data["order"]["grantedRefunds"][0]
    assert granted_refund_assigned_to_order == data["grantedRefund"]
    assert granted_refund_assigned_to_order["reason"] == reason == granted_refund.reason
    assert granted_refund.amount_value == current_amount


def test_grant_refund_update_by_app_missing_permission(
    app_api_client, staff_user, order
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        user=staff_user,
    )

    amount = Decimal("10.00")
    reason = "Granted refund reason."
    variables = {
        "id": to_global_id_or_none(granted_refund),
        "input": {"amount": amount, "reason": reason},
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    assert_no_permission(response)


def test_grant_refund_update_by_app_missing_input(
    app_api_client, staff_user, order, permission_manage_orders
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        user=staff_user,
    )

    variables = {
        "id": to_global_id_or_none(granted_refund),
        "input": {},
    }
    app_api_client.app.permissions.set([permission_manage_orders])

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    content = get_graphql_content_from_response(response)
    errors = content["data"]["orderGrantRefundUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderGrantRefundUpdateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "input"
