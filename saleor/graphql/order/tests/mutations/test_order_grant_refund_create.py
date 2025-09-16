from decimal import Decimal

import graphene
import pytest

from .....core.prices import quantize_price
from .....order.utils import update_order_charge_data
from .....page.models import Page, PageType
from ....core.utils import to_global_id_or_none
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
)
from ...enums import (
    OrderChargeStatusEnum,
    OrderGrantedRefundStatusEnum,
    OrderGrantRefundCreateErrorCode,
    OrderGrantRefundCreateLineErrorCode,
)

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
      reasonReference { id }
      user{
        id
      }
      app{
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
    order{
      id
      chargeStatus
      grantedRefunds{
        id
        amount{
          amount
        }
        createdAt
        updatedAt
        reason
        reasonReference { id }
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
    errors{
      field
      code
      lines{
        field
        code
        lineId
        message
      }
    }
  }
}
"""


@pytest.mark.parametrize("reason", ["", "Reason", None])
def test_grant_refund_by_user(
    reason,
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
):
    # given
    order_id = to_global_id_or_none(order)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": reason,
            "transactionId": transaction_item_id,
        },
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
    reason = reason or ""
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

    assert (
        granted_refund_assigned_to_order["status"]
        == OrderGrantedRefundStatusEnum.NONE.name
    )
    assert granted_refund_assigned_to_order["transactionEvents"] == []
    assert granted_refund_assigned_to_order["transaction"]["id"] == transaction_item_id


@pytest.mark.parametrize("reason", ["", "Reason", None])
def test_grant_refund_by_app(
    reason, app_api_client, permission_manage_orders, order, transaction_item_generator
):
    # given
    order_id = to_global_id_or_none(order)
    app_api_client.app.permissions.set([permission_manage_orders])
    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )
    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": reason,
            "transactionId": transaction_item_id,
        },
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
    reason = reason or ""
    assert granted_refund["reason"] == reason == granted_refund_from_db.reason
    assert not granted_refund["user"]
    assert (
        granted_refund["app"]["id"]
        == to_global_id_or_none(app_api_client.app)
        == to_global_id_or_none(granted_refund_from_db.app)
    )

    assert granted_refund["status"] == OrderGrantedRefundStatusEnum.NONE.name
    assert granted_refund["transactionEvents"] == []
    assert granted_refund["transaction"]["id"] == transaction_item_id


def test_grant_refund_by_app_missing_permission(
    app_api_client, order, transaction_item_generator
):
    # given
    order_id = to_global_id_or_none(order)
    amount = Decimal("10.00")
    reason = "Granted refund reason."
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )
    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": reason,
            "transactionId": transaction_item_id,
        },
    }

    # when
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    assert_no_permission(response)


def test_grant_refund_by_user_missing_permission(
    staff_api_client, order, transaction_item_generator
):
    # given
    order_id = to_global_id_or_none(order)
    amount = Decimal("10.00")
    reason = "Granted refund reason."
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )
    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": reason,
            "transactionId": transaction_item_id,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    assert_no_permission(response)


def test_grant_refund_incorrect_order_id(
    staff_api_client, permission_manage_orders, transaction_item_generator, order
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    amount = Decimal("10.00")
    reason = "Granted refund reason."
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )
    variables = {
        "id": "wrong-id",
        "input": {
            "amount": amount,
            "reason": reason,
            "transactionId": transaction_item_id,
        },
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


def test_grant_refund_with_only_include_grant_refund_for_shipping(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    order_id = to_global_id_or_none(order)
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    amount = Decimal(20)
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )
    variables = {
        "id": order_id,
        "input": {
            "grantRefundForShipping": True,
            "transactionId": transaction_item_id,
        },
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
    granted_refund_from_db = order_with_lines.granted_refunds.first()
    order_granted_refund = data["order"]["grantedRefunds"][0]
    assert (
        granted_refund_from_db.shipping_costs_included
        == order_granted_refund["shippingCostsIncluded"]
        is True
    )
    assert data["grantedRefund"]["shippingCostsIncluded"] is True
    assert (
        granted_refund_from_db.amount_value
        == order_with_lines.shipping_price_gross_amount
    )


def test_grant_refund_with_only_lines(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    order_id = to_global_id_or_none(order)
    first_line = order.lines.first()
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    charged_amount = Decimal("20.0")
    transaction_item = transaction_item_generator(
        charged_value=charged_amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )
    expected_reason = "Reason"
    variables = {
        "id": order_id,
        "input": {
            "lines": [
                {
                    "id": to_global_id_or_none(first_line),
                    "quantity": 1,
                    "reason": expected_reason,
                },
            ],
            "transactionId": transaction_item_id,
        },
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
    order_granted_refund = data["order"]["grantedRefunds"][0]
    assert data["grantedRefund"]["shippingCostsIncluded"] is False
    assert len(order_granted_refund["lines"]) == 1
    assert order_granted_refund["lines"][0]["quantity"] == 1
    assert order_granted_refund["lines"][0]["orderLine"]["id"] == to_global_id_or_none(
        first_line
    )
    assert order_granted_refund["lines"][0]["reason"] == expected_reason

    assert granted_refund_from_db.amount_value == first_line.unit_price_gross_amount * 1
    assert quantize_price(
        granted_refund_from_db.amount_value, order.currency
    ) == quantize_price(
        Decimal(order_granted_refund["amount"]["amount"]), order.currency
    )
    granted_refund_line = granted_refund_from_db.lines.first()
    assert granted_refund_line.order_line == first_line
    assert granted_refund_line.quantity == 1
    assert granted_refund_line.reason == expected_reason


def test_grant_refund_with_include_grant_refund_for_shipping_and_lines(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    order_id = to_global_id_or_none(order)
    first_line = order.lines.first()
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    charged_amount = Decimal("30.0")
    transaction_item = transaction_item_generator(
        charged_value=charged_amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )
    variables = {
        "id": order_id,
        "input": {
            "grantRefundForShipping": True,
            "lines": [{"id": to_global_id_or_none(first_line), "quantity": 1}],
            "transactionId": transaction_item_id,
        },
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
    order_granted_refund = data["order"]["grantedRefunds"][0]
    assert (
        granted_refund_from_db.shipping_costs_included
        == order_granted_refund["shippingCostsIncluded"]
        is True
    )
    assert data["grantedRefund"]["shippingCostsIncluded"] is True
    assert len(order_granted_refund["lines"]) == 1
    assert order_granted_refund["lines"][0]["quantity"] == 1
    assert order_granted_refund["lines"][0]["orderLine"]["id"] == to_global_id_or_none(
        first_line
    )
    assert granted_refund_from_db.amount_value == (
        first_line.unit_price_gross_amount * 1 + order.shipping_price_gross_amount
    )
    assert quantize_price(
        granted_refund_from_db.amount_value, order.currency
    ) == quantize_price(
        Decimal(order_granted_refund["amount"]["amount"]), order.currency
    )
    granted_refund_line = granted_refund_from_db.lines.first()
    assert granted_refund_line.order_line == first_line
    assert granted_refund_line.quantity == 1


def test_grant_refund_with_provided_lines_shipping_and_amount(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    order_id = to_global_id_or_none(order)
    first_line = order.lines.first()
    expected_amount = Decimal("10.0")
    transaction_item = transaction_item_generator(
        charged_value=expected_amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    variables = {
        "id": order_id,
        "input": {
            "grantRefundForShipping": True,
            "lines": [{"id": to_global_id_or_none(first_line), "quantity": 1}],
            "amount": expected_amount,
            "transactionId": transaction_item_id,
        },
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
    order_granted_refund = data["order"]["grantedRefunds"][0]
    assert (
        granted_refund_from_db.shipping_costs_included
        == order_granted_refund["shippingCostsIncluded"]
        is True
    )
    assert data["grantedRefund"]["shippingCostsIncluded"] is True
    assert len(order_granted_refund["lines"]) == 1
    assert order_granted_refund["lines"][0]["quantity"] == 1
    assert order_granted_refund["lines"][0]["orderLine"]["id"] == to_global_id_or_none(
        first_line
    )
    assert granted_refund_from_db.amount_value == expected_amount
    assert quantize_price(
        granted_refund_from_db.amount_value, order.currency
    ) == quantize_price(
        Decimal(order_granted_refund["amount"]["amount"]), order.currency
    )
    granted_refund_line = granted_refund_from_db.lines.first()
    assert granted_refund_line.order_line == first_line
    assert granted_refund_line.quantity == 1


def test_grant_refund_without_lines_and_amount_and_grant_for_shipping(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    order_id = to_global_id_or_none(order)
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    charged_amount = Decimal("10.0")
    transaction_item = transaction_item_generator(
        charged_value=charged_amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )
    variables = {
        "id": order_id,
        "input": {
            "reason": "Reason",
            "transactionId": transaction_item_id,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 3
    assert {error["field"] for error in errors} == {
        "amount",
        "lines",
        "grantRefundForShipping",
    }
    assert {error["code"] for error in errors} == {"REQUIRED"}


def test_grant_refund_with_incorrect_line_id(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    order_id = to_global_id_or_none(order)
    charged_amount = Decimal("10.0")
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    transaction_item = transaction_item_generator(
        charged_value=charged_amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )
    variables = {
        "id": order_id,
        "input": {
            "lines": [
                {"id": graphene.Node.to_global_id("OrderLine", 1), "quantity": 1}
            ],
            "transactionId": transaction_item_id,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "lines"
    assert error["code"] == OrderGrantRefundCreateErrorCode.INVALID.name
    assert len(error["lines"]) == 1
    line = error["lines"][0]
    assert line["lineId"] == graphene.Node.to_global_id("OrderLine", 1)
    assert line["field"] == "id"
    assert line["code"] == OrderGrantRefundCreateLineErrorCode.GRAPHQL_ERROR.name


def test_grant_refund_with_line_that_belongs_to_another_order(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    order_with_lines_for_cc,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    another_order = order_with_lines_for_cc
    another_order_id = to_global_id_or_none(another_order)
    first_line = order.lines.first()
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    charged_amount = Decimal("10.0")
    transaction_item = transaction_item_generator(
        charged_value=charged_amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )
    variables = {
        "id": another_order_id,
        "input": {
            "lines": [{"id": to_global_id_or_none(first_line), "quantity": 1}],
            "transactionId": transaction_item_id,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "lines"
    assert error["code"] == OrderGrantRefundCreateErrorCode.INVALID.name
    assert len(error["lines"]) == 1
    line = error["lines"][0]
    assert line["lineId"] == to_global_id_or_none(first_line)
    assert line["field"] == "id"
    assert line["code"] == OrderGrantRefundCreateLineErrorCode.NOT_FOUND.name


def test_grant_refund_with_bigger_quantity_than_available(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    order_id = to_global_id_or_none(order)
    first_line = order.lines.first()
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    charged_amount = Decimal("10.0")
    transaction_item = transaction_item_generator(
        charged_value=charged_amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )
    variables = {
        "id": order_id,
        "input": {
            "lines": [{"id": to_global_id_or_none(first_line), "quantity": 100}],
            "transactionId": transaction_item_id,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "lines"
    assert error["code"] == OrderGrantRefundCreateErrorCode.INVALID.name
    assert len(error["lines"]) == 1
    line = error["lines"][0]
    assert line["lineId"] == to_global_id_or_none(first_line)
    assert line["field"] == "quantity"
    assert (
        line["code"]
        == OrderGrantRefundCreateLineErrorCode.QUANTITY_GREATER_THAN_AVAILABLE.name
    )


def test_grant_refund_with_refund_for_shipping_already_processed(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    order_id = to_global_id_or_none(order)
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    charged_amount = Decimal("10.0")
    transaction_item = transaction_item_generator(
        charged_value=charged_amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )
    variables = {
        "id": order_id,
        "input": {
            "grantRefundForShipping": True,
            "transactionId": transaction_item_id,
        },
    }
    order.granted_refunds.create(shipping_costs_included=True)

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "grantRefundForShipping"
    assert (
        error["code"]
        == OrderGrantRefundCreateErrorCode.SHIPPING_COSTS_ALREADY_GRANTED.name
    )


def test_grant_refund_with_lines_and_existing_other_grant_refund(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    order_id = to_global_id_or_none(order)
    first_line = order.lines.first()
    first_line.quantity = 2
    first_line.save(update_fields=["quantity"])

    charged_amount = Decimal("20.0")
    transaction_item = transaction_item_generator(
        charged_value=charged_amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    variables = {
        "id": order_id,
        "input": {
            "lines": [{"id": to_global_id_or_none(first_line), "quantity": 1}],
            "transactionId": transaction_item_id,
        },
    }
    granted_refund = order.granted_refunds.create(shipping_costs_included=False)
    granted_refund.lines.create(order_line=first_line, quantity=1)

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert not errors

    assert order_id == data["order"]["id"]
    assert len(data["order"]["grantedRefunds"]) == 2

    granted_refund_from_db = order.granted_refunds.last()
    order_granted_refund = data["order"]["grantedRefunds"][1]
    assert data["grantedRefund"]["shippingCostsIncluded"] is False
    assert len(order_granted_refund["lines"]) == 1
    assert order_granted_refund["lines"][0]["quantity"] == 1
    assert order_granted_refund["lines"][0]["orderLine"]["id"] == to_global_id_or_none(
        first_line
    )
    assert granted_refund_from_db.amount_value == first_line.unit_price_gross_amount * 1
    assert quantize_price(
        granted_refund_from_db.amount_value, order.currency
    ) == quantize_price(
        Decimal(order_granted_refund["amount"]["amount"]), order.currency
    )


def test_grant_refund_with_lines_and_existing_other_grant_and_refund_exceeding_quantity(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    order_id = to_global_id_or_none(order)
    first_line = order.lines.first()
    first_line.quantity = 1
    first_line.save(update_fields=["quantity"])

    charged_amount = Decimal("10.0")
    transaction_item = transaction_item_generator(
        charged_value=charged_amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    variables = {
        "id": order_id,
        "input": {
            "lines": [{"id": to_global_id_or_none(first_line), "quantity": 1}],
            "transactionId": transaction_item_id,
        },
    }
    granted_refund = order.granted_refunds.create(shipping_costs_included=False)
    granted_refund.lines.create(order_line=first_line, quantity=1)

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "lines"
    assert error["code"] == OrderGrantRefundCreateErrorCode.INVALID.name
    assert len(error["lines"]) == 1
    line = error["lines"][0]
    assert line["lineId"] == to_global_id_or_none(first_line)
    assert line["field"] == "quantity"
    assert (
        line["code"]
        == OrderGrantRefundCreateLineErrorCode.QUANTITY_GREATER_THAN_AVAILABLE.name
    )


def test_grant_refund_updates_order_charge_status(
    staff_api_client, permission_manage_orders, order_with_lines
):
    # given
    order = order_with_lines
    order_id = to_global_id_or_none(order)
    amount = Decimal("10.00")
    authorized_value = Decimal(12)
    transaction_item = order.payment_transactions.create(
        charged_value=order.total.gross.amount,
        authorized_value=authorized_value,
        currency=order_with_lines.currency,
    )
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    reason = "Granted refund reason."
    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": reason,
            "transactionId": transaction_item_id,
        },
    }
    update_order_charge_data(order)
    assert order.charge_status == OrderChargeStatusEnum.FULL.value

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert not errors

    assert order_id == data["order"]["id"]
    assert len(data["order"]["grantedRefunds"]) == 1

    assert data["order"]["chargeStatus"] == OrderChargeStatusEnum.OVERCHARGED.name


def test_grant_refund_with_transaction_item_and_without_input_amount(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    expected_granted_amount = Decimal("1.23")
    transaction_item = transaction_item_generator(
        charged_value=expected_granted_amount, order_id=order.id
    )
    order_id = to_global_id_or_none(order)
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    first_line = order.lines.first()
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    expected_reason = "Reason"
    variables = {
        "id": order_id,
        "input": {
            "transactionId": transaction_item_id,
            "lines": [
                {
                    "id": to_global_id_or_none(first_line),
                    "quantity": 1,
                    "reason": expected_reason,
                },
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert not errors

    granted_refund_from_db = order.granted_refunds.first()
    assert granted_refund_from_db.amount_value == expected_granted_amount
    assert granted_refund_from_db.transaction_item == transaction_item

    assert order_id == data["order"]["id"]
    assert len(data["order"]["grantedRefunds"]) == 1

    order_granted_refund = data["order"]["grantedRefunds"][0]
    assert data["grantedRefund"]["shippingCostsIncluded"] is False
    assert len(order_granted_refund["lines"]) == 1
    assert order_granted_refund["lines"][0]["quantity"] == 1
    assert order_granted_refund["lines"][0]["orderLine"]["id"] == to_global_id_or_none(
        first_line
    )
    assert order_granted_refund["lines"][0]["reason"] == expected_reason

    assert order_granted_refund["status"] == OrderGrantedRefundStatusEnum.NONE.name
    assert order_granted_refund["transactionEvents"] == []
    assert order_granted_refund["transaction"]["id"] == transaction_item_id

    assert quantize_price(
        granted_refund_from_db.amount_value, order.currency
    ) == quantize_price(
        Decimal(order_granted_refund["amount"]["amount"]), order.currency
    )
    granted_refund_line = granted_refund_from_db.lines.first()
    assert granted_refund_line.order_line == first_line
    assert granted_refund_line.quantity == 1
    assert granted_refund_line.reason == expected_reason


def test_grant_refund_with_transaction_item_and_amount_greater_than_charged_amount(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    expected_granted_amount = Decimal("1.23")
    transaction_item = transaction_item_generator(
        charged_value=expected_granted_amount, order_id=order.id
    )
    order_id = to_global_id_or_none(order)
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    first_line = order.lines.first()
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    expected_reason = "Reason"
    variables = {
        "id": order_id,
        "input": {
            "amount": expected_granted_amount + 1,
            "transactionId": transaction_item_id,
            "lines": [
                {
                    "id": to_global_id_or_none(first_line),
                    "quantity": 1,
                    "reason": expected_reason,
                },
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert (
        error["code"]
        == OrderGrantRefundCreateErrorCode.AMOUNT_GREATER_THAN_AVAILABLE.name
    )
    assert error["field"] == "amount"


@pytest.mark.parametrize("expected_granted_amount", [Decimal("1.23"), Decimal("1.00")])
def test_grant_refund_with_transaction_item_and_amount(
    expected_granted_amount,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    expected_charged_amount = Decimal("1.23")
    transaction_item = transaction_item_generator(
        charged_value=expected_charged_amount, order_id=order.id
    )
    order_id = to_global_id_or_none(order)
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    first_line = order.lines.first()
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    expected_reason = "Reason"
    variables = {
        "id": order_id,
        "input": {
            "amount": expected_granted_amount,
            "transactionId": transaction_item_id,
            "lines": [
                {
                    "id": to_global_id_or_none(first_line),
                    "quantity": 1,
                    "reason": expected_reason,
                },
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert not errors

    granted_refund_from_db = order.granted_refunds.first()
    assert granted_refund_from_db.amount_value == expected_granted_amount
    assert granted_refund_from_db.transaction_item == transaction_item

    assert order_id == data["order"]["id"]
    assert len(data["order"]["grantedRefunds"]) == 1

    order_granted_refund = data["order"]["grantedRefunds"][0]
    assert data["grantedRefund"]["shippingCostsIncluded"] is False
    assert len(order_granted_refund["lines"]) == 1
    assert order_granted_refund["lines"][0]["quantity"] == 1
    assert order_granted_refund["lines"][0]["orderLine"]["id"] == to_global_id_or_none(
        first_line
    )
    assert order_granted_refund["lines"][0]["reason"] == expected_reason

    assert order_granted_refund["status"] == OrderGrantedRefundStatusEnum.NONE.name
    assert order_granted_refund["transactionEvents"] == []
    assert order_granted_refund["transaction"]["id"] == transaction_item_id

    assert quantize_price(
        granted_refund_from_db.amount_value, order.currency
    ) == quantize_price(
        Decimal(order_granted_refund["amount"]["amount"]), order.currency
    )
    granted_refund_line = granted_refund_from_db.lines.first()
    assert granted_refund_line.order_line == first_line
    assert granted_refund_line.quantity == 1
    assert granted_refund_line.reason == expected_reason


# Reason reference tests


def test_grant_refund_with_reference_required_created_by_user(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )

    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order_id = to_global_id_or_none(order)
    page_id = to_global_id_or_none(page)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "reasonReference": page_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
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
        granted_refund_assigned_to_order["reasonReference"]["id"]
        == page_id
        == to_global_id_or_none(granted_refund_from_db.reason_reference)
    )
    assert granted_refund_from_db.reason_reference == page


def test_grant_refund_with_reference_required_but_not_provided_created_by_user(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order_id = to_global_id_or_none(order)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == OrderGrantRefundCreateErrorCode.REQUIRED.name

    assert order.granted_refunds.count() == 0


def test_grant_refund_with_reference_required_but_not_provided_created_by_app(
    app_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order_id = to_global_id_or_none(order)
    app_api_client.app.permissions.set([permission_manage_orders])

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert not errors

    assert order_id == data["order"]["id"]
    assert len(data["order"]["grantedRefunds"]) == 1
    granted_refund_from_db = order.granted_refunds.first()
    granted_refund_assigned_to_order = data["order"]["grantedRefunds"][0]
    assert granted_refund_assigned_to_order == data["grantedRefund"]

    assert granted_refund_assigned_to_order["reasonReference"] is None
    assert granted_refund_from_db.reason_reference is None


def test_grant_refund_with_reference_not_enabled_created_by_user_rejected(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )

    assert site_settings.refund_reason_reference_type is None

    order_id = to_global_id_or_none(order)
    page_id = to_global_id_or_none(page)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "reasonReference": page_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]

    assert len(errors) == 1

    error = errors[0]

    assert error["field"] == "reasonReference"
    assert error["code"] == OrderGrantRefundCreateErrorCode.INVALID.name


def test_grant_refund_with_reference_not_enabled_created_by_app_rejects(
    app_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )

    assert site_settings.refund_reason_reference_type is None

    order_id = to_global_id_or_none(order)
    page_id = to_global_id_or_none(page)
    app_api_client.app.permissions.set([permission_manage_orders])

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "reasonReference": page_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = app_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == OrderGrantRefundCreateErrorCode.INVALID.name


def test_grant_refund_with_reference_required_created_by_user_throws_for_invalid_id(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order_id = to_global_id_or_none(order)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    invalid_page_id = graphene.Node.to_global_id("Page", 99999)
    assert Page.objects.count() == 0

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "reasonReference": invalid_page_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == OrderGrantRefundCreateErrorCode.INVALID.name

    assert order.granted_refunds.count() == 0


def test_grant_refund_with_reason_reference_wrong_page_type_created_by_user(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
):
    # Given
    page_type1 = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type1
    site_settings.save()

    page_type2 = PageType.objects.create(name="Different Type", slug="different-type")
    page_wrong_type = Page.objects.create(
        slug="wrong-type-page",
        title="Wrong Type Page",
        page_type=page_type2,
        is_published=True,
    )

    order_id = to_global_id_or_none(order)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    wrong_page_id = to_global_id_or_none(page_wrong_type)

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "reasonReference": wrong_page_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == OrderGrantRefundCreateErrorCode.INVALID.name

    assert order.granted_refunds.count() == 0


def test_grant_refund_with_reason_reference_not_valid_page_id(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order_id = to_global_id_or_none(order)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    invalid_page_id = graphene.Node.to_global_id("Product", 12345)

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "reasonReference": invalid_page_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]

    assert error["field"] == "reasonReference"
    assert error["code"] == "GRAPHQL_ERROR"

    assert order.granted_refunds.count() == 0


def test_grant_refund_with_reason_reference_not_valid_id_created_by_user(
    staff_api_client,
    permission_manage_orders,
    order,
    transaction_item_generator,
    site_settings,
):
    # Given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    order_id = to_global_id_or_none(order)
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    amount = Decimal("10.00")
    transaction_item = transaction_item_generator(
        charged_value=amount, order_id=order.id
    )
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    # Use a completely invalid ID format
    invalid_id = "invalid-id-format"

    variables = {
        "id": order_id,
        "input": {
            "amount": amount,
            "reason": "Damaged product refund",
            "reasonReference": invalid_id,
            "transactionId": transaction_item_id,
        },
    }

    # When
    response = staff_api_client.post_graphql(ORDER_GRANT_REFUND_CREATE, variables)

    # Then
    content = get_graphql_content(response)
    data = content["data"]["orderGrantRefundCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == "GRAPHQL_ERROR"

    assert order.granted_refunds.count() == 0
