from decimal import Decimal

from saleor.core.prices import quantize_price

from ....core.utils import to_global_id_or_none
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ...enums import (
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


def test_grant_refund_update_include_grant_refund_for_shipping(
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
