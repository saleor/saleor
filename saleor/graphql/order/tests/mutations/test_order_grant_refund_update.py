from decimal import Decimal

import graphene
import pytest

from .....core.prices import quantize_price
from .....order import OrderGrantedRefundStatus
from .....order.utils import update_order_charge_data
from ....core.utils import to_global_id_or_none
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ...enums import (
    OrderChargeStatusEnum,
    OrderGrantedRefundStatusEnum,
    OrderGrantRefundUpdateErrorCode,
    OrderGrantRefundUpdateLineErrorCode,
)

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
      shippingCostsIncluded
      lines{
        id
        orderLine{
          id
        }
        quantity
        reason
      }
      status
      transactionEvents{
        id
      }
      transaction{
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
        shippingCostsIncluded
        lines{
          id
          orderLine{
            id
          }
          quantity
          reason
        }
        status
        transactionEvents{
          id
        }
        transaction{
          id
        }
      }
    }
    errors {
      field
      code
      message
      addLines{
        field
        code
        lineId
        message
      }
      removeLines{
        field
        code
        lineId
        message
      }
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
    assert (
        granted_refund_assigned_to_order["status"]
        == OrderGrantedRefundStatusEnum.NONE.name
    )
    assert granted_refund_assigned_to_order["transactionEvents"] == []
    assert not granted_refund_assigned_to_order["transaction"]


@pytest.mark.parametrize("amount", [Decimal("0.00"), Decimal("20.00")])
def test_grant_refund_update_only_amount_by_user(
    amount, staff_api_client, app, permission_manage_orders, order
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


@pytest.mark.parametrize("reason", ["", "new reason"])
def test_grant_refund_update_only_reason_by_user(
    reason, staff_api_client, app, permission_manage_orders, order
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
    assert (
        granted_refund_assigned_to_order["status"]
        == OrderGrantedRefundStatusEnum.NONE.name
    )
    assert granted_refund_assigned_to_order["transactionEvents"] == []
    assert not granted_refund_assigned_to_order["transaction"]


@pytest.mark.parametrize("amount", [Decimal("0.00"), Decimal("20.00")])
def test_grant_refund_update_only_amount_by_app(
    amount, app_api_client, staff_user, permission_manage_orders, order
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


@pytest.mark.parametrize("reason", ["", "new reason"])
def test_grant_refund_update_only_reason_by_app(
    reason, app_api_client, staff_user, permission_manage_orders, order
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


@pytest.mark.parametrize("current_include_shipping", [True, False])
def test_grant_refund_update_include_grant_refund_for_shipping(
    current_include_shipping,
    app_api_client,
    staff_user,
    permission_manage_orders,
    order_with_lines,
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
        shipping_costs_included=current_include_shipping,
    )
    granted_refund_id = to_global_id_or_none(granted_refund)
    app_api_client.app.permissions.set([permission_manage_orders])

    variables = {
        "id": granted_refund_id,
        "input": {"grantRefundForShipping": True},
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]

    granted_refund_assigned_to_order = data["order"]["grantedRefunds"][0]
    assert granted_refund_assigned_to_order["id"] == data["grantedRefund"]["id"]
    granted_refund.refresh_from_db()
    assert (
        granted_refund.shipping_costs_included
        == granted_refund_assigned_to_order["shippingCostsIncluded"]
        is True
    )
    assert granted_refund_assigned_to_order["shippingCostsIncluded"] is True
    assert granted_refund.amount_value == order_with_lines.shipping_price_gross_amount
    assert quantize_price(
        granted_refund.amount_value, order_with_lines.currency
    ) == quantize_price(
        Decimal(granted_refund_assigned_to_order["amount"]["amount"]),
        order_with_lines.currency,
    )


def test_grant_refund_update_with_only_add_lines(
    app_api_client, staff_user, permission_manage_orders, order_with_lines
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    order_line = order_with_lines.lines.first()
    granted_refund_id = to_global_id_or_none(granted_refund)
    app_api_client.app.permissions.set([permission_manage_orders])

    expected_quantity = 1
    expected_reason = "Reason"

    variables = {
        "id": granted_refund_id,
        "input": {
            "addLines": [
                {
                    "id": to_global_id_or_none(order_line),
                    "quantity": expected_quantity,
                    "reason": expected_reason,
                }
            ]
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]
    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_data = data["order"]["grantedRefunds"][0]
    assert len(granted_refund_data["lines"]) == 1
    assert granted_refund_data["lines"][0]["orderLine"]["id"] == to_global_id_or_none(
        order_line
    )
    assert granted_refund_data["lines"][0]["quantity"] == expected_quantity
    assert granted_refund_data["lines"][0]["reason"] == expected_reason

    assert len(granted_refund.lines.all()) == 1
    granted_refund_line = granted_refund.lines.first()
    assert granted_refund_line.order_line == order_line
    assert granted_refund_line.quantity == expected_quantity
    assert granted_refund_line.reason == expected_reason

    assert (
        granted_refund.amount_value
        == order_line.unit_price_gross_amount * expected_quantity
    )
    assert quantize_price(
        granted_refund.amount_value, order_with_lines.currency
    ) == quantize_price(
        Decimal(granted_refund_data["amount"]["amount"]), order_with_lines.currency
    )


def test_grant_refund_update_with_only_remove_lines(
    app_api_client, staff_user, permission_manage_orders, order_with_lines
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    order_line = order_with_lines.lines.first()
    granted_refund_line = granted_refund.lines.create(order_line=order_line, quantity=1)
    granted_refund_line_id = to_global_id_or_none(granted_refund_line)
    granted_refund_id = to_global_id_or_none(granted_refund)
    app_api_client.app.permissions.set([permission_manage_orders])

    variables = {
        "id": granted_refund_id,
        "input": {"removeLines": [granted_refund_line_id]},
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]

    assert not data["errors"]

    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_data = data["order"]["grantedRefunds"][0]
    assert len(granted_refund_data["lines"]) == 0
    assert len(granted_refund.lines.all()) == 0

    assert granted_refund.amount_value == 0
    assert quantize_price(
        granted_refund.amount_value, order_with_lines.currency
    ) == quantize_price(
        Decimal(granted_refund_data["amount"]["amount"]), order_with_lines.currency
    )


def test_grant_refund_update_with_add_and_remove_lines(
    app_api_client, staff_user, permission_manage_orders, order_with_lines
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    last_order_line = order_with_lines.lines.last()
    granted_refund_line_to_remove = granted_refund.lines.create(
        order_line=last_order_line, quantity=1
    )

    order_line = order_with_lines.lines.first()
    granted_refund_id = to_global_id_or_none(granted_refund)
    app_api_client.app.permissions.set([permission_manage_orders])

    expected_quantity = 1

    variables = {
        "id": granted_refund_id,
        "input": {
            "addLines": [
                {"id": to_global_id_or_none(order_line), "quantity": expected_quantity}
            ],
            "removeLines": [to_global_id_or_none(granted_refund_line_to_remove)],
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]
    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_data = data["order"]["grantedRefunds"][0]
    assert len(granted_refund_data["lines"]) == 1
    assert granted_refund_data["lines"][0]["orderLine"]["id"] == to_global_id_or_none(
        order_line
    )

    assert len(granted_refund.lines.all()) == 1
    granted_refund_line = granted_refund.lines.first()
    assert granted_refund_line.order_line == order_line
    assert granted_refund_line.quantity == expected_quantity

    assert (
        granted_refund.amount_value
        == order_line.unit_price_gross_amount * expected_quantity
    )
    assert quantize_price(
        granted_refund.amount_value, order_with_lines.currency
    ) == quantize_price(
        Decimal(granted_refund_data["amount"]["amount"]), order_with_lines.currency
    )


def test_grant_refund_update_with_same_line_in_add_and_remove(
    app_api_client, staff_user, permission_manage_orders, order_with_lines
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    last_order_line = order_with_lines.lines.last()
    last_order_line.quantity = 2
    last_order_line.save()
    granted_refund_line_to_remove = granted_refund.lines.create(
        order_line=last_order_line, quantity=1
    )

    granted_refund_id = to_global_id_or_none(granted_refund)
    app_api_client.app.permissions.set([permission_manage_orders])

    expected_quantity = 2

    variables = {
        "id": granted_refund_id,
        "input": {
            "addLines": [
                {
                    "id": to_global_id_or_none(last_order_line),
                    "quantity": expected_quantity,
                }
            ],
            "removeLines": [to_global_id_or_none(granted_refund_line_to_remove)],
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]
    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_data = data["order"]["grantedRefunds"][0]
    assert len(granted_refund_data["lines"]) == 1
    assert granted_refund_data["lines"][0]["orderLine"]["id"] == to_global_id_or_none(
        last_order_line
    )

    assert len(granted_refund.lines.all()) == 1
    granted_refund_line = granted_refund.lines.first()
    assert granted_refund_line.order_line == last_order_line
    assert granted_refund_line.quantity == expected_quantity

    assert (
        granted_refund.amount_value
        == last_order_line.unit_price_gross_amount * expected_quantity
    )
    assert quantize_price(
        granted_refund.amount_value, order_with_lines.currency
    ) == quantize_price(
        Decimal(granted_refund_data["amount"]["amount"]), order_with_lines.currency
    )


def test_grant_refund_update_with_add_and_remove_lines_and_shipping_included(
    app_api_client, staff_user, permission_manage_orders, order_with_lines
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    last_order_line = order_with_lines.lines.last()
    granted_refund_line_to_remove = granted_refund.lines.create(
        order_line=last_order_line, quantity=1
    )

    order_line = order_with_lines.lines.first()
    granted_refund_id = to_global_id_or_none(granted_refund)
    app_api_client.app.permissions.set([permission_manage_orders])

    expected_quantity = 1

    variables = {
        "id": granted_refund_id,
        "input": {
            "addLines": [
                {"id": to_global_id_or_none(order_line), "quantity": expected_quantity}
            ],
            "removeLines": [to_global_id_or_none(granted_refund_line_to_remove)],
            "grantRefundForShipping": True,
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]
    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_data = data["order"]["grantedRefunds"][0]
    assert len(granted_refund_data["lines"]) == 1
    assert granted_refund_data["lines"][0]["orderLine"]["id"] == to_global_id_or_none(
        order_line
    )

    assert len(granted_refund.lines.all()) == 1
    granted_refund_line = granted_refund.lines.first()
    assert granted_refund_line.order_line == order_line
    assert granted_refund_line.quantity == expected_quantity

    assert (
        granted_refund.amount_value
        == order_line.unit_price_gross_amount * expected_quantity
        + order_with_lines.shipping_price_gross_amount
    )
    assert quantize_price(
        granted_refund.amount_value, order_with_lines.currency
    ) == quantize_price(
        Decimal(granted_refund_data["amount"]["amount"]), order_with_lines.currency
    )


def test_grant_refund_update_with_add_and_remove_lines_and_shipping_included_and_amount(
    app_api_client, staff_user, permission_manage_orders, order_with_lines
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    last_order_line = order_with_lines.lines.last()
    granted_refund_line_to_remove = granted_refund.lines.create(
        order_line=last_order_line, quantity=1
    )

    order_line = order_with_lines.lines.first()
    granted_refund_id = to_global_id_or_none(granted_refund)
    app_api_client.app.permissions.set([permission_manage_orders])

    expected_quantity = 1
    expected_amount = Decimal("20.000")

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": expected_amount,
            "addLines": [
                {"id": to_global_id_or_none(order_line), "quantity": expected_quantity}
            ],
            "removeLines": [to_global_id_or_none(granted_refund_line_to_remove)],
            "grantRefundForShipping": True,
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]
    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_data = data["order"]["grantedRefunds"][0]
    assert len(granted_refund_data["lines"]) == 1
    assert granted_refund_data["lines"][0]["orderLine"]["id"] == to_global_id_or_none(
        order_line
    )

    assert len(granted_refund.lines.all()) == 1
    granted_refund_line = granted_refund.lines.first()
    assert granted_refund_line.order_line == order_line
    assert granted_refund_line.quantity == expected_quantity

    assert granted_refund.amount_value == expected_amount
    assert quantize_price(
        granted_refund.amount_value, order_with_lines.currency
    ) == quantize_price(
        Decimal(granted_refund_data["amount"]["amount"]), order_with_lines.currency
    )


def test_grant_refund_update_with_incorrect_add_line_id(
    app_api_client, staff_user, permission_manage_orders, order_with_lines
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    granted_refund_id = to_global_id_or_none(granted_refund)
    app_api_client.app.permissions.set([permission_manage_orders])

    expected_quantity = 1

    variables = {
        "id": granted_refund_id,
        "input": {"addLines": [{"id": "incorrect-id", "quantity": expected_quantity}]},
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "addLines"
    assert error["code"] == OrderGrantRefundUpdateErrorCode.INVALID.name
    assert len(error["addLines"]) == 1
    line = error["addLines"][0]
    assert line["lineId"] == "incorrect-id"
    assert line["field"] == "id"
    assert line["code"] == OrderGrantRefundUpdateLineErrorCode.GRAPHQL_ERROR.name
    assert len(granted_refund.lines.all()) == 0


def test_grant_refund_update_with_incorrect_remove_line_id(
    app_api_client, staff_user, permission_manage_orders, order_with_lines
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    order_line = order_with_lines.lines.first()
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    granted_refund_line = granted_refund.lines.create(order_line=order_line, quantity=1)

    granted_refund_id = to_global_id_or_none(granted_refund)
    app_api_client.app.permissions.set([permission_manage_orders])

    variables = {
        "id": granted_refund_id,
        "input": {"removeLines": ["incorrect-id"]},
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "removeLines"
    assert error["code"] == OrderGrantRefundUpdateErrorCode.INVALID.name
    assert len(error["removeLines"]) == 1
    line = error["removeLines"][0]
    assert line["lineId"] == "incorrect-id"
    assert line["field"] is None
    assert line["code"] == OrderGrantRefundUpdateLineErrorCode.GRAPHQL_ERROR.name
    assert len(granted_refund.lines.all()) == 1
    assert granted_refund.lines.all()[0] == granted_refund_line


def test_grant_refund_update_with_add_line_belongs_to_another_order(
    app_api_client,
    staff_user,
    permission_manage_orders,
    order_with_lines,
    order_with_lines_for_cc,
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    order_line_from_another_order = order_with_lines_for_cc.lines.first()
    granted_refund_id = to_global_id_or_none(granted_refund)
    order_line_from_another_order_id = to_global_id_or_none(
        order_line_from_another_order
    )
    app_api_client.app.permissions.set([permission_manage_orders])

    expected_quantity = 1

    variables = {
        "id": granted_refund_id,
        "input": {
            "addLines": [
                {"id": order_line_from_another_order_id, "quantity": expected_quantity}
            ]
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "addLines"
    assert error["code"] == OrderGrantRefundUpdateErrorCode.INVALID.name
    assert len(error["addLines"]) == 1
    line = error["addLines"][0]
    assert line["lineId"] == order_line_from_another_order_id
    assert line["field"] == "id"
    assert line["code"] == OrderGrantRefundUpdateLineErrorCode.NOT_FOUND.name
    assert len(granted_refund.lines.all()) == 0


def test_grant_refund_update_with_remove_line_belong_to_another_granted_refund(
    app_api_client, staff_user, permission_manage_orders, order_with_lines
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    order_line = order_with_lines.lines.first()
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    granted_refund_line = granted_refund.lines.create(order_line=order_line, quantity=1)

    second_granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )

    second_granted_refund_id = to_global_id_or_none(second_granted_refund)
    granted_refund_line_id = to_global_id_or_none(granted_refund_line)

    app_api_client.app.permissions.set([permission_manage_orders])

    variables = {
        "id": second_granted_refund_id,
        "input": {"removeLines": [granted_refund_line_id]},
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "removeLines"
    assert error["code"] == OrderGrantRefundUpdateErrorCode.INVALID.name
    assert len(error["removeLines"]) == 1
    line = error["removeLines"][0]
    assert line["lineId"] == granted_refund_line_id
    assert line["field"] is None
    assert line["code"] == OrderGrantRefundUpdateLineErrorCode.NOT_FOUND.name


def test_grant_refund_update_with_add_line_quantity_bigger_than_order_line_quantity(
    app_api_client, staff_user, permission_manage_orders, order_with_lines
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    order_line = order_with_lines.lines.first()
    granted_refund_id = to_global_id_or_none(granted_refund)
    order_line_id = to_global_id_or_none(order_line)
    app_api_client.app.permissions.set([permission_manage_orders])

    expected_quantity = 100

    variables = {
        "id": granted_refund_id,
        "input": {"addLines": [{"id": order_line_id, "quantity": expected_quantity}]},
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "addLines"
    assert error["code"] == OrderGrantRefundUpdateErrorCode.INVALID.name
    assert len(error["addLines"]) == 1
    line = error["addLines"][0]
    assert line["lineId"] == order_line_id
    assert line["field"] == "quantity"
    assert (
        line["code"]
        == OrderGrantRefundUpdateLineErrorCode.QUANTITY_GREATER_THAN_AVAILABLE.name
    )
    assert len(granted_refund.lines.all()) == 0


def test_grant_refund_update_with_add_line_quantity_bigger_than_available_quantity(
    app_api_client, staff_user, permission_manage_orders, order_with_lines
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    order_line = order_with_lines.lines.first()
    second_granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    second_granted_refund.lines.create(
        order_line=order_line, quantity=order_line.quantity
    )
    granted_refund_id = to_global_id_or_none(granted_refund)
    order_line_id = to_global_id_or_none(order_line)
    app_api_client.app.permissions.set([permission_manage_orders])

    expected_quantity = 1

    variables = {
        "id": granted_refund_id,
        "input": {"addLines": [{"id": order_line_id, "quantity": expected_quantity}]},
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "addLines"
    assert error["code"] == OrderGrantRefundUpdateErrorCode.INVALID.name
    assert len(error["addLines"]) == 1
    line = error["addLines"][0]
    assert line["lineId"] == order_line_id
    assert line["field"] == "quantity"
    assert (
        line["code"]
        == OrderGrantRefundUpdateLineErrorCode.QUANTITY_GREATER_THAN_AVAILABLE.name
    )
    assert len(granted_refund.lines.all()) == 0


def test_grant_refund_update_with_shipping_cost_already_included(
    app_api_client, staff_user, permission_manage_orders, order_with_lines
):
    # given
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    order_line = order_with_lines.lines.first()
    order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
        shipping_costs_included=True,
    )
    granted_refund_id = to_global_id_or_none(granted_refund)
    order_line_id = to_global_id_or_none(order_line)
    app_api_client.app.permissions.set([permission_manage_orders])

    expected_quantity = 1

    variables = {
        "id": granted_refund_id,
        "input": {
            "addLines": [{"id": order_line_id, "quantity": expected_quantity}],
            "grantRefundForShipping": True,
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "grantRefundForShipping"
    assert (
        error["code"]
        == OrderGrantRefundUpdateErrorCode.SHIPPING_COSTS_ALREADY_GRANTED.name
    )
    assert len(granted_refund.lines.all()) == 0


def test_grant_refund_updates_order_charge_status(
    staff_api_client, app, permission_manage_orders, order_with_lines
):
    # given
    order = order_with_lines
    new_granted_refund_amount = Decimal("5.00")
    order.payment_transactions.create(
        charged_value=order.total.gross.amount - new_granted_refund_amount,
        authorized_value=Decimal(12),
        currency=order_with_lines.currency,
    )
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

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": new_granted_refund_amount,
        },
    }
    update_order_charge_data(order)

    # overcharged as total(98.40) - current grantedRefund(10.00) is less than
    # total charged(98.40 - 5.00)
    assert order.charge_status == OrderChargeStatusEnum.OVERCHARGED.value

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    order.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]

    assert data["order"]["id"] == to_global_id_or_none(order)
    assert len(data["order"]["grantedRefunds"]) == 1

    assert order.charge_status == OrderChargeStatusEnum.FULL.value


def test_grant_refund_update_with_transaction_item(
    staff_api_client, app, permission_manage_orders, order, transaction_item_generator
):
    # given
    transaction_item = transaction_item_generator(
        order_id=order.id, charged_value=Decimal("22.00")
    )
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

    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )
    variables = {
        "id": granted_refund_id,
        "input": {"transactionId": transaction_item_id},
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
    assert granted_refund.transaction_item == transaction_item
    assert granted_refund.updated_at.isoformat() == data["grantedRefund"]["updatedAt"]
    assert (
        granted_refund_assigned_to_order["amount"]["amount"]
        == granted_refund.amount_value
    )
    assert granted_refund_assigned_to_order["reason"] == granted_refund.reason
    assert granted_refund_assigned_to_order["app"]["id"] == to_global_id_or_none(
        granted_refund.app
    )
    assert (
        granted_refund_assigned_to_order["status"]
        == OrderGrantedRefundStatusEnum.NONE.name
    )
    assert granted_refund_assigned_to_order["transactionEvents"] == []
    assert granted_refund_assigned_to_order["transaction"]["id"] == transaction_item_id


@pytest.mark.parametrize("expected_granted_amount", [Decimal("2.00"), Decimal("1.00")])
def test_grant_refund_update_with_transaction_and_correct_amount(
    expected_granted_amount,
    staff_api_client,
    app,
    permission_manage_orders,
    order,
    transaction_item_generator,
):
    # given
    transaction_item = transaction_item_generator(
        order_id=order.id, charged_value=Decimal("2.00")
    )
    current_reason = "Granted refund reason."
    granted_refund = order.granted_refunds.create(
        amount_value=expected_granted_amount,
        currency=order.currency,
        reason=current_reason,
        app=app,
    )
    updated_at = granted_refund.updated_at
    granted_refund_id = to_global_id_or_none(granted_refund)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )
    variables = {
        "id": granted_refund_id,
        "input": {
            "transactionId": graphene.Node.to_global_id(
                "TransactionItem", transaction_item.token
            )
        },
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
    assert granted_refund.transaction_item == transaction_item
    assert granted_refund.updated_at.isoformat() == data["grantedRefund"]["updatedAt"]
    assert (
        granted_refund_assigned_to_order["amount"]["amount"]
        == granted_refund.amount_value
    )
    assert granted_refund_assigned_to_order["reason"] == granted_refund.reason
    assert granted_refund_assigned_to_order["app"]["id"] == to_global_id_or_none(
        granted_refund.app
    )
    assert (
        granted_refund_assigned_to_order["status"]
        == OrderGrantedRefundStatusEnum.NONE.name
    )
    assert granted_refund_assigned_to_order["transactionEvents"] == []
    assert granted_refund_assigned_to_order["transaction"]["id"] == transaction_item_id


def test_grant_refund_update_with_input_amount_greater_than_transaction_charged_amount(
    staff_api_client, app, permission_manage_orders, order, transaction_item_generator
):
    # given
    charged_value = Decimal("10.00")
    transaction_item = transaction_item_generator(
        order_id=order.id, charged_value=charged_value
    )
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
    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": charged_value + Decimal("1.00"),
            "transactionId": transaction_id,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "amount"
    assert (
        error["code"]
        == OrderGrantRefundUpdateErrorCode.AMOUNT_GREATER_THAN_AVAILABLE.name
    )


def test_grant_refund_update_with_transaction_granted_amount_is_bigger_than_charged(
    staff_api_client, app, permission_manage_orders, order, transaction_item_generator
):
    # given
    charged_value = Decimal("0.00")
    transaction_item = transaction_item_generator(
        order_id=order.id, charged_value=charged_value
    )
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
    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {"transactionId": transaction_id},
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "transactionId"
    assert (
        error["code"]
        == OrderGrantRefundUpdateErrorCode.AMOUNT_GREATER_THAN_AVAILABLE.name
    )


@pytest.mark.parametrize("input_amount", [Decimal("1.00"), Decimal("2.00")])
def test_grant_refund_update_with_correct_input_amount_to_transaction_charged_amount(
    input_amount,
    staff_api_client,
    app,
    permission_manage_orders,
    order,
    transaction_item_generator,
):
    # given
    transaction_item = transaction_item_generator(
        order_id=order.id, charged_value=Decimal("2.00")
    )
    current_reason = "Granted refund reason."
    granted_refund = order.granted_refunds.create(
        amount_value=Decimal("0.50"),
        currency=order.currency,
        reason=current_reason,
        app=app,
    )
    updated_at = granted_refund.updated_at
    granted_refund_id = to_global_id_or_none(granted_refund)
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {"transactionId": transaction_id, "amount": input_amount},
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
    assert granted_refund.transaction_item == transaction_item
    assert granted_refund.updated_at.isoformat() == data["grantedRefund"]["updatedAt"]
    assert (
        granted_refund_assigned_to_order["amount"]["amount"]
        == granted_refund.amount_value
    )
    assert granted_refund_assigned_to_order["reason"] == granted_refund.reason
    assert granted_refund_assigned_to_order["app"]["id"] == to_global_id_or_none(
        granted_refund.app
    )
    assert (
        granted_refund_assigned_to_order["status"]
        == OrderGrantedRefundStatusEnum.NONE.name
    )
    assert granted_refund_assigned_to_order["transactionEvents"] == []
    assert granted_refund_assigned_to_order["transaction"]["id"] == transaction_id


def test_grant_refund_update_with_transaction_and_add_lines(
    transaction_item_generator,
    app_api_client,
    staff_user,
    permission_manage_orders,
    order_with_lines,
):
    # given
    max_granted_charged_value = Decimal("1.00")
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.id, charged_value=max_granted_charged_value
    )
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    order_line = order_with_lines.lines.first()
    granted_refund_id = to_global_id_or_none(granted_refund)
    app_api_client.app.permissions.set([permission_manage_orders])

    expected_quantity = 1
    expected_reason = "Reason"

    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {
            "transactionId": transaction_id,
            "addLines": [
                {
                    "id": to_global_id_or_none(order_line),
                    "quantity": expected_quantity,
                    "reason": expected_reason,
                }
            ],
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert not data["errors"]
    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_data = data["order"]["grantedRefunds"][0]
    assert len(granted_refund_data["lines"]) == 1
    assert granted_refund_data["lines"][0]["orderLine"]["id"] == to_global_id_or_none(
        order_line
    )
    assert granted_refund_data["lines"][0]["quantity"] == expected_quantity
    assert granted_refund_data["lines"][0]["reason"] == expected_reason

    assert len(granted_refund.lines.all()) == 1
    granted_refund_line = granted_refund.lines.first()
    assert granted_refund_line.order_line == order_line
    assert granted_refund_line.quantity == expected_quantity
    assert granted_refund_line.reason == expected_reason

    assert granted_refund.amount_value == max_granted_charged_value
    assert quantize_price(
        granted_refund.amount_value, order_with_lines.currency
    ) == quantize_price(
        Decimal(granted_refund_data["amount"]["amount"]), order_with_lines.currency
    )
    assert granted_refund_data["status"] == OrderGrantedRefundStatusEnum.NONE.name
    assert granted_refund_data["transactionEvents"] == []
    assert granted_refund_data["transaction"]["id"] == transaction_id


def test_grant_refund_update_with_transaction_and_remove_lines(
    app_api_client,
    staff_user,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    max_granted_charged_value = Decimal("1.00")
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.id, charged_value=max_granted_charged_value
    )
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    order_line = order_with_lines.lines.first()
    granted_refund_line = granted_refund.lines.create(order_line=order_line, quantity=1)
    granted_refund_line_id = to_global_id_or_none(granted_refund_line)
    granted_refund_id = to_global_id_or_none(granted_refund)

    second_order_line = order_with_lines.lines.last()
    granted_refund.lines.create(order_line=second_order_line, quantity=1)

    app_api_client.app.permissions.set([permission_manage_orders])

    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {
            "transactionId": transaction_id,
            "removeLines": [granted_refund_line_id],
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]

    assert not data["errors"]

    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_data = data["order"]["grantedRefunds"][0]

    assert granted_refund.amount_value == max_granted_charged_value
    assert quantize_price(
        granted_refund.amount_value, order_with_lines.currency
    ) == quantize_price(
        Decimal(granted_refund_data["amount"]["amount"]), order_with_lines.currency
    )
    assert granted_refund_data["status"] == OrderGrantedRefundStatusEnum.NONE.name
    assert granted_refund_data["transactionEvents"] == []
    assert granted_refund_data["transaction"]["id"] == transaction_id


def test_grant_refund_update_with_transaction_and_shipping_and_add_and_remove_lines(
    app_api_client,
    staff_user,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    max_granted_charged_value = Decimal("1.00")
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.id, charged_value=max_granted_charged_value
    )
    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    order_line = order_with_lines.lines.first()
    granted_refund_line = granted_refund.lines.create(order_line=order_line, quantity=1)
    granted_refund_line_id = to_global_id_or_none(granted_refund_line)
    granted_refund_id = to_global_id_or_none(granted_refund)

    second_order_line = order_with_lines.lines.last()

    app_api_client.app.permissions.set([permission_manage_orders])

    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {
            "transactionId": transaction_id,
            "removeLines": [granted_refund_line_id],
            "addLines": [
                {
                    "id": to_global_id_or_none(second_order_line),
                    "quantity": 1,
                }
            ],
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]

    assert not data["errors"]

    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_data = data["order"]["grantedRefunds"][0]

    assert granted_refund.amount_value == max_granted_charged_value
    assert quantize_price(
        granted_refund.amount_value, order_with_lines.currency
    ) == quantize_price(
        Decimal(granted_refund_data["amount"]["amount"]), order_with_lines.currency
    )
    assert granted_refund_data["status"] == OrderGrantedRefundStatusEnum.NONE.name
    assert granted_refund_data["transactionEvents"] == []
    assert granted_refund_data["transaction"]["id"] == transaction_id


def test_grant_refund_update_with_transaction_add_remove_lines_shipping_invalid_amount(
    app_api_client,
    staff_user,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    max_granted_charged_value = Decimal("1.00")
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.id, charged_value=max_granted_charged_value
    )
    current_reason = "Granted refund reason."
    current_amount = Decimal("0.50")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    order_line = order_with_lines.lines.first()
    granted_refund_line = granted_refund.lines.create(order_line=order_line, quantity=1)
    granted_refund_line_id = to_global_id_or_none(granted_refund_line)
    granted_refund_id = to_global_id_or_none(granted_refund)

    second_order_line = order_with_lines.lines.last()

    app_api_client.app.permissions.set([permission_manage_orders])

    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": Decimal("20.00"),
            "transactionId": transaction_id,
            "grantRefundForShipping": True,
            "removeLines": [granted_refund_line_id],
            "addLines": [
                {
                    "id": to_global_id_or_none(second_order_line),
                    "quantity": 1,
                }
            ],
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]

    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "amount"
    assert (
        error["code"]
        == OrderGrantRefundUpdateErrorCode.AMOUNT_GREATER_THAN_AVAILABLE.name
    )


def test_grant_refund_update_with_transaction_add_remove_lines_shipping_amount(
    app_api_client,
    staff_user,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    max_granted_charged_value = Decimal("1.00")
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.id, charged_value=max_granted_charged_value
    )
    current_reason = "Granted refund reason."
    current_amount = Decimal("0.50")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    order_line = order_with_lines.lines.first()
    granted_refund_line = granted_refund.lines.create(order_line=order_line, quantity=1)
    granted_refund_line_id = to_global_id_or_none(granted_refund_line)
    granted_refund_id = to_global_id_or_none(granted_refund)

    second_order_line = order_with_lines.lines.last()

    app_api_client.app.permissions.set([permission_manage_orders])

    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": max_granted_charged_value,
            "transactionId": transaction_id,
            "grantRefundForShipping": True,
            "removeLines": [granted_refund_line_id],
            "addLines": [
                {
                    "id": to_global_id_or_none(second_order_line),
                    "quantity": 1,
                }
            ],
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]

    assert not data["errors"]

    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_data = data["order"]["grantedRefunds"][0]

    assert granted_refund.amount_value == max_granted_charged_value
    assert quantize_price(
        granted_refund.amount_value, order_with_lines.currency
    ) == quantize_price(
        Decimal(granted_refund_data["amount"]["amount"]), order_with_lines.currency
    )

    assert granted_refund_data["status"] == OrderGrantedRefundStatusEnum.NONE.name
    assert granted_refund_data["transactionEvents"] == []
    assert granted_refund_data["transaction"]["id"] == transaction_id


def test_grant_refund_update_with_transaction_add_lines_and_invalid_amount(
    app_api_client,
    staff_user,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    max_granted_charged_value = Decimal("1.00")
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.id, charged_value=max_granted_charged_value
    )
    current_reason = "Granted refund reason."
    current_amount = Decimal("0.50")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    granted_refund_id = to_global_id_or_none(granted_refund)

    second_order_line = order_with_lines.lines.last()

    app_api_client.app.permissions.set([permission_manage_orders])

    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": max_granted_charged_value + Decimal("1.00"),
            "transactionId": transaction_id,
            "addLines": [
                {
                    "id": to_global_id_or_none(second_order_line),
                    "quantity": 1,
                }
            ],
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]

    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "amount"
    assert (
        error["code"]
        == OrderGrantRefundUpdateErrorCode.AMOUNT_GREATER_THAN_AVAILABLE.name
    )


def test_grant_refund_update_with_transaction_remove_lines_and_invalid_amount(
    app_api_client,
    staff_user,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    max_granted_charged_value = Decimal("1.00")
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.id, charged_value=max_granted_charged_value
    )
    current_reason = "Granted refund reason."
    current_amount = Decimal("0.50")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    order_line = order_with_lines.lines.first()
    granted_refund_line = granted_refund.lines.create(order_line=order_line, quantity=1)
    granted_refund_line_id = to_global_id_or_none(granted_refund_line)
    granted_refund_id = to_global_id_or_none(granted_refund)

    app_api_client.app.permissions.set([permission_manage_orders])

    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": max_granted_charged_value + Decimal("1.00"),
            "transactionId": transaction_id,
            "grantRefundForShipping": True,
            "removeLines": [granted_refund_line_id],
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]

    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "amount"
    assert (
        error["code"]
        == OrderGrantRefundUpdateErrorCode.AMOUNT_GREATER_THAN_AVAILABLE.name
    )


def test_grant_refund_update_with_transaction_granted_shipping_and_invalid_amount(
    app_api_client,
    staff_user,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    max_granted_charged_value = Decimal("1.00")
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.id, charged_value=max_granted_charged_value
    )
    current_reason = "Granted refund reason."
    current_amount = Decimal("0.50")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
    )
    granted_refund_id = to_global_id_or_none(granted_refund)

    app_api_client.app.permissions.set([permission_manage_orders])

    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": max_granted_charged_value + Decimal("1.00"),
            "transactionId": transaction_id,
            "grantRefundForShipping": True,
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]

    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "amount"
    assert (
        error["code"]
        == OrderGrantRefundUpdateErrorCode.AMOUNT_GREATER_THAN_AVAILABLE.name
    )


@pytest.mark.parametrize(
    "granted_refund_status",
    [OrderGrantedRefundStatus.SUCCESS, OrderGrantedRefundStatus.PENDING],
)
def test_granted_refund_update_when_status_blocks_action(
    granted_refund_status,
    app_api_client,
    staff_user,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    max_granted_charged_value = Decimal("1.00")
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.id, charged_value=max_granted_charged_value
    )
    current_reason = "Granted refund reason."
    current_amount = Decimal("0.50")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
        status=granted_refund_status,
    )
    granted_refund_id = to_global_id_or_none(granted_refund)

    app_api_client.app.permissions.set([permission_manage_orders])

    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": max_granted_charged_value,
            "transactionId": transaction_id,
            "grantRefundForShipping": True,
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]
    assert len(data["errors"]) == 3
    error_fields = {error["field"] for error in data["errors"]}
    error_codes = {error["code"] for error in data["errors"]}
    assert error_codes == {OrderGrantRefundUpdateErrorCode.INVALID.name}
    assert error_fields == {"amount", "transactionId", "grantRefundForShipping"}


@pytest.mark.parametrize(
    "granted_refund_status",
    [OrderGrantedRefundStatus.FAILURE, OrderGrantedRefundStatus.NONE],
)
def test_granted_refund_update_when_status_allows_update(
    granted_refund_status,
    app_api_client,
    staff_user,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    max_granted_charged_value = Decimal("1.00")
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.id, charged_value=max_granted_charged_value
    )
    current_reason = "Granted refund reason."
    current_amount = Decimal("0.50")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
        status=granted_refund_status,
    )
    order_line = order_with_lines.lines.first()
    granted_refund_line = granted_refund.lines.create(order_line=order_line, quantity=1)
    granted_refund_line_id = to_global_id_or_none(granted_refund_line)
    granted_refund_id = to_global_id_or_none(granted_refund)

    second_order_line = order_with_lines.lines.last()

    app_api_client.app.permissions.set([permission_manage_orders])

    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": granted_refund_id,
        "input": {
            "amount": max_granted_charged_value,
            "transactionId": transaction_id,
            "grantRefundForShipping": True,
            "removeLines": [granted_refund_line_id],
            "addLines": [
                {
                    "id": to_global_id_or_none(second_order_line),
                    "quantity": 1,
                }
            ],
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]

    assert not data["errors"]

    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_data = data["order"]["grantedRefunds"][0]

    assert granted_refund.amount_value == max_granted_charged_value
    assert quantize_price(
        granted_refund.amount_value, order_with_lines.currency
    ) == quantize_price(
        Decimal(granted_refund_data["amount"]["amount"]), order_with_lines.currency
    )


@pytest.mark.parametrize(
    "granted_refund_status",
    [OrderGrantedRefundStatus.SUCCESS, OrderGrantedRefundStatus.PENDING],
)
def test_granted_refund_updated_when_status_blocks_action_and_only_reason_provided(
    granted_refund_status,
    app_api_client,
    staff_user,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    max_granted_charged_value = Decimal("1.00")
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.id, charged_value=max_granted_charged_value
    )
    current_reason = "Granted refund reason."
    current_amount = Decimal("0.50")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=current_amount,
        currency=order_with_lines.currency,
        reason=current_reason,
        user=staff_user,
        status=granted_refund_status,
        transaction_item=transaction_item,
    )
    granted_refund_id = to_global_id_or_none(granted_refund)

    app_api_client.app.permissions.set([permission_manage_orders])

    expected_reason = "New reason"
    variables = {
        "id": granted_refund_id,
        "input": {"reason": expected_reason},
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_UPDATE, variables)

    # then
    granted_refund.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundUpdate"]

    assert not data["errors"]

    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_data = data["order"]["grantedRefunds"][0]

    assert granted_refund.reason == expected_reason
    assert granted_refund_data["reason"] == expected_reason
