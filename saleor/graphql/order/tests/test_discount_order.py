from decimal import Decimal
from functools import partial
from unittest.mock import patch

import graphene
import pytest
from prices import Money, TaxedMoney, fixed_discount, percentage_discount

from ....core.prices import quantize_price
from ....discount import DiscountValueType
from ....order import OrderEvents, OrderStatus
from ....order.error_codes import OrderErrorCode
from ...discount.enums import DiscountValueTypeEnum
from ...tests.utils import get_graphql_content

ORDER_DISCOUNT_ADD = """
mutation OrderDiscountAdd($orderId: ID!, $input: OrderDiscountCommonInput!){
  orderDiscountAdd(orderId:$orderId, input:$input){
    order{
      lines{
        id
      }
      total{
        gross{
          amount
        }
        net{
          amount
        }
      }
    }
    orderErrors{
      field
      code
      message
    }
  }
}
"""


@pytest.mark.parametrize(
    "value,value_type",
    [
        (Decimal("2222222"), DiscountValueTypeEnum.FIXED.name),
        (Decimal("101"), DiscountValueTypeEnum.PERCENTAGE.name),
    ],
)
def test_add_order_discount_incorrect_values(
    value, value_type, draft_order, staff_api_client, permission_manage_orders
):
    variables = {
        "orderId": graphene.Node.to_global_id("Order", draft_order.pk),
        "input": {"valueType": value_type, "value": value},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountAdd"]

    errors = data["orderErrors"]

    error = data["orderErrors"][0]
    assert error["field"] == "value"
    assert error["code"] == OrderErrorCode.INVALID.name

    assert len(errors) == 1


def test_add_fixed_order_discount_order_is_not_draft(
    order_with_lines, staff_api_client, permission_manage_orders
):
    value = Decimal("10")
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "input": {"valueType": DiscountValueTypeEnum.FIXED.name, "value": value},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountAdd"]

    errors = data["orderErrors"]
    assert len(errors) == 1
    error = data["orderErrors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == OrderErrorCode.CANNOT_DISCOUNT.name


def test_add_fixed_order_discount_to_order(
    draft_order, staff_api_client, permission_manage_orders
):
    total_before_order_discount = draft_order.total
    value = Decimal("10")
    variables = {
        "orderId": graphene.Node.to_global_id("Order", draft_order.pk),
        "input": {"valueType": DiscountValueTypeEnum.FIXED.name, "value": value},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountAdd"]

    draft_order.refresh_from_db()
    expected_gross = total_before_order_discount.gross.amount - value
    expected_net = total_before_order_discount.net.amount - value

    errors = data["orderErrors"]
    assert len(errors) == 0

    assert expected_gross == draft_order.total.gross.amount
    assert expected_net == draft_order.total.net.amount

    assert draft_order.undiscounted_total == total_before_order_discount

    assert draft_order.discounts.count() == 1
    order_discount = draft_order.discounts.first()
    assert order_discount.value == value
    assert order_discount.value_type == DiscountValueType.FIXED
    assert order_discount.amount.amount == value
    assert order_discount.reason is None

    event = draft_order.events.get()
    assert event.type == OrderEvents.ORDER_DISCOUNT_ADDED
    parameters = event.parameters
    discount_data = parameters.get("discount")

    assert discount_data["value"] == str(value)
    assert discount_data["value_type"] == DiscountValueTypeEnum.FIXED.value
    assert discount_data["amount_value"] == str(order_discount.amount.amount)


def test_add_percentage_order_discount_to_order(
    draft_order, staff_api_client, permission_manage_orders
):
    total_before_order_discount = draft_order.total
    reason = "The reason of the discount"
    value = Decimal("10.000")
    variables = {
        "orderId": graphene.Node.to_global_id("Order", draft_order.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.PERCENTAGE.name,
            "value": value,
            "reason": reason,
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountAdd"]

    draft_order.refresh_from_db()

    discount = partial(percentage_discount, percentage=value)
    expected_net_total = discount(total_before_order_discount.net)
    expected_gross_total = discount(total_before_order_discount.gross)
    expected_total = TaxedMoney(expected_net_total, expected_gross_total)

    errors = data["orderErrors"]
    assert len(errors) == 0

    assert expected_total == draft_order.total

    assert draft_order.undiscounted_total == total_before_order_discount

    assert draft_order.discounts.count() == 1
    order_discount = draft_order.discounts.first()
    assert order_discount.value == value
    assert order_discount.value_type == DiscountValueType.PERCENTAGE
    assert order_discount.amount == (total_before_order_discount - expected_total).gross
    assert order_discount.reason == reason

    event = draft_order.events.get()
    assert event.type == OrderEvents.ORDER_DISCOUNT_ADDED
    parameters = event.parameters
    discount_data = parameters.get("discount")

    assert discount_data["value"] == str(value)
    assert discount_data["value_type"] == DiscountValueTypeEnum.PERCENTAGE.value
    assert discount_data["amount_value"] == str(order_discount.amount.amount)


ORDER_DISCOUNT_UPDATE = """
mutation OrderDiscountUpdate($discountId: ID!, $input: OrderDiscountCommonInput!){
  orderDiscountUpdate(discountId:$discountId, input: $input){
    order{
      id
      total{
        gross{
          amount
        }
      }
      undiscountedTotal{
        gross{
          amount
        }
      }
    }
    orderErrors{
        field
        message
        code
      }
  }
}
"""


def test_update_percentage_order_discount_to_order(
    draft_order_with_fixed_discount_order, staff_api_client, permission_manage_orders
):
    draft_order = draft_order_with_fixed_discount_order
    order_discount = draft_order_with_fixed_discount_order.discounts.get()
    current_undiscounted_total = draft_order.undiscounted_total

    reason = "The reason of the discount"
    value = Decimal("10.000")
    variables = {
        "discountId": graphene.Node.to_global_id("OrderDiscount", order_discount.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.PERCENTAGE.name,
            "value": value,
            "reason": reason,
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountUpdate"]

    draft_order.refresh_from_db()

    discount = partial(percentage_discount, percentage=value)
    expected_net_total = discount(current_undiscounted_total.net)
    expected_gross_total = discount(current_undiscounted_total.gross)
    expected_total = TaxedMoney(expected_net_total, expected_gross_total)

    errors = data["orderErrors"]
    assert len(errors) == 0

    assert draft_order.undiscounted_total == current_undiscounted_total

    assert expected_total == draft_order.total

    assert draft_order.discounts.count() == 1
    order_discount = draft_order.discounts.first()
    assert order_discount.value == value
    assert order_discount.value_type == DiscountValueType.PERCENTAGE
    assert order_discount.amount == (current_undiscounted_total - expected_total).gross
    assert order_discount.reason == reason

    event = draft_order.events.get()
    assert event.type == OrderEvents.ORDER_DISCOUNT_UPDATED
    parameters = event.parameters
    discount_data = parameters.get("discount")

    assert discount_data["value"] == str(value)
    assert discount_data["value_type"] == DiscountValueTypeEnum.PERCENTAGE.value
    assert discount_data["amount_value"] == str(order_discount.amount.amount)


def test_update_fixed_order_discount_to_order(
    draft_order_with_fixed_discount_order, staff_api_client, permission_manage_orders
):
    draft_order = draft_order_with_fixed_discount_order
    order_discount = draft_order_with_fixed_discount_order.discounts.get()
    current_undiscounted_total = draft_order.undiscounted_total

    value = Decimal("50.000")
    variables = {
        "discountId": graphene.Node.to_global_id("OrderDiscount", order_discount.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.FIXED.name,
            "value": value,
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountUpdate"]

    draft_order.refresh_from_db()

    discount = partial(
        fixed_discount, discount=Money(value, currency=draft_order.currency)
    )
    expected_total = discount(current_undiscounted_total)

    errors = data["orderErrors"]
    assert len(errors) == 0

    assert draft_order.undiscounted_total == current_undiscounted_total

    assert expected_total == draft_order.total

    assert draft_order.discounts.count() == 1
    order_discount = draft_order.discounts.first()
    assert order_discount.value == value
    assert order_discount.value_type == DiscountValueType.FIXED
    assert order_discount.amount == (current_undiscounted_total - expected_total).gross

    event = draft_order.events.get()
    assert event.type == OrderEvents.ORDER_DISCOUNT_UPDATED
    parameters = event.parameters
    discount_data = parameters.get("discount")

    assert discount_data["value"] == str(value)
    assert discount_data["value_type"] == DiscountValueTypeEnum.FIXED.value
    assert discount_data["amount_value"] == str(order_discount.amount.amount)


def test_update_order_discount_order_is_not_draft(
    draft_order_with_fixed_discount_order, staff_api_client, permission_manage_orders
):
    draft_order_with_fixed_discount_order.status = OrderStatus.UNFULFILLED
    draft_order_with_fixed_discount_order.save()

    order_discount = draft_order_with_fixed_discount_order.discounts.get()

    value = Decimal("50")
    variables = {
        "discountId": graphene.Node.to_global_id("OrderDiscount", order_discount.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.FIXED.name,
            "value": value,
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountUpdate"]

    errors = data["orderErrors"]
    assert len(errors) == 1

    error = data["orderErrors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == OrderErrorCode.CANNOT_DISCOUNT.name


@pytest.mark.parametrize(
    "value,value_type",
    [
        (Decimal("2222222"), DiscountValueTypeEnum.FIXED.name),
        (Decimal("101"), DiscountValueTypeEnum.PERCENTAGE.name),
    ],
)
def test_update_order_discount_incorrect_values(
    value,
    value_type,
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_manage_orders,
):
    order_discount = draft_order_with_fixed_discount_order.discounts.get()

    variables = {
        "discountId": graphene.Node.to_global_id("OrderDiscount", order_discount.pk),
        "input": {
            "valueType": value_type,
            "value": value,
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountUpdate"]

    errors = data["orderErrors"]
    assert len(errors) == 1

    error = errors[0]
    assert error["field"] == "value"
    assert error["code"] == OrderErrorCode.INVALID.name


ORDER_DISCOUNT_DELETE = """
mutation OrderDiscountDelete($discountId: ID!){
  orderDiscountDelete(discountId: $discountId){
    order{
      id
    }
    orderErrors{
      field
      message
      code
    }
  }
}
"""


def test_delete_order_discount_from_order(
    draft_order_with_fixed_discount_order, staff_api_client, permission_manage_orders
):
    draft_order = draft_order_with_fixed_discount_order
    order_discount = draft_order_with_fixed_discount_order.discounts.get()
    current_undiscounted_total = draft_order.undiscounted_total

    variables = {
        "discountId": graphene.Node.to_global_id("OrderDiscount", order_discount.pk),
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_DELETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountDelete"]

    draft_order.refresh_from_db()

    errors = data["orderErrors"]
    assert len(errors) == 0

    assert draft_order.undiscounted_total == current_undiscounted_total
    assert draft_order.total == current_undiscounted_total

    event = draft_order.events.get()
    assert event.type == OrderEvents.ORDER_DISCOUNT_DELETED


def test_delete_order_discount_order_is_not_draft(
    draft_order_with_fixed_discount_order, staff_api_client, permission_manage_orders
):
    draft_order_with_fixed_discount_order.status = OrderStatus.UNFULFILLED
    draft_order_with_fixed_discount_order.save()

    order_discount = draft_order_with_fixed_discount_order.discounts.get()

    variables = {
        "discountId": graphene.Node.to_global_id("OrderDiscount", order_discount.pk),
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_DELETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountDelete"]

    errors = data["orderErrors"]
    assert len(errors) == 1

    assert draft_order_with_fixed_discount_order.discounts.get()

    error = data["orderErrors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == OrderErrorCode.CANNOT_DISCOUNT.name


ORDER_LINE_DISCOUNT_UPDATE = """
mutation OrderLineDiscountUpdate($input: OrderDiscountCommonInput!, $orderLineId: ID!){
  orderLineDiscountUpdate(orderLineId: $orderLineId, input: $input){
    orderLine{
      unitPrice{
        gross{
          amount
        }
      }
    }
    orderErrors{
      field
      message
      code
    }
  }
}
"""


def test_update_order_line_discount(
    draft_order_with_fixed_discount_order, staff_api_client, permission_manage_orders
):
    line_to_discount = draft_order_with_fixed_discount_order.lines.first()
    unit_price = Money(Decimal(7.3), currency="USD")
    line_to_discount.unit_price = TaxedMoney(unit_price, unit_price)
    line_to_discount.save()

    line_price_before_discount = line_to_discount.unit_price

    value = Decimal("5")
    reason = "New reason for unit discount"
    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line_to_discount.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.FIXED.name,
            "value": value,
            "reason": reason,
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountUpdate"]

    line_to_discount.refresh_from_db()

    errors = data["orderErrors"]
    assert not errors

    discount = partial(
        fixed_discount,
        discount=Money(value, currency=draft_order_with_fixed_discount_order.currency),
    )
    expected_line_price = discount(line_price_before_discount)

    assert line_to_discount.unit_price == quantize_price(expected_line_price, "USD")
    unit_discount = line_to_discount.unit_discount
    assert unit_discount == (line_price_before_discount - expected_line_price).gross

    event = draft_order_with_fixed_discount_order.events.get()
    assert event.type == OrderEvents.ORDER_LINE_DISCOUNT_UPDATED
    parameters = event.parameters
    lines = parameters.get("lines", {})
    assert len(lines) == 1

    line_data = lines[0]
    assert line_data.get("line_pk") == line_to_discount.pk
    discount_data = line_data.get("discount")

    assert discount_data["value"] == str(value)
    assert discount_data["value_type"] == DiscountValueTypeEnum.FIXED.value
    assert discount_data["amount_value"] == str(unit_discount.amount)


def test_update_order_line_discount_line_with_discount(
    draft_order_with_fixed_discount_order, staff_api_client, permission_manage_orders
):
    line_to_discount = draft_order_with_fixed_discount_order.lines.first()
    unit_price = quantize_price(Money(Decimal(7.3), currency="USD"), currency="USD")
    line_to_discount.unit_price = TaxedMoney(unit_price, unit_price)

    line_to_discount.unit_discount_amount = Decimal("2.500")
    line_to_discount.unit_discount_type = DiscountValueType.FIXED
    line_to_discount.unit_discount_value = Decimal("2.500")
    line_to_discount.save()

    line_discount_amount_before_update = line_to_discount.unit_discount_amount
    line_discount_value_before_update = line_to_discount.unit_discount_value

    line_undiscounted_price = line_to_discount.undiscounted_unit_price

    value = Decimal("50")
    reason = "New reason for unit discount"
    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line_to_discount.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.PERCENTAGE.name,
            "value": value,
            "reason": reason,
        },
    }

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountUpdate"]

    line_to_discount.refresh_from_db()

    errors = data["orderErrors"]
    assert not errors

    discount = partial(
        percentage_discount,
        percentage=value,
    )
    expected_line_price = discount(line_undiscounted_price)

    assert line_to_discount.unit_price == expected_line_price
    unit_discount = line_to_discount.unit_discount
    assert unit_discount == (line_undiscounted_price - expected_line_price).gross

    event = draft_order_with_fixed_discount_order.events.get()
    assert event.type == OrderEvents.ORDER_LINE_DISCOUNT_UPDATED
    parameters = event.parameters
    lines = parameters.get("lines", {})
    assert len(lines) == 1

    line_data = lines[0]
    assert line_data.get("line_pk") == line_to_discount.pk
    discount_data = line_data.get("discount")

    assert discount_data["value"] == str(value)
    assert discount_data["value_type"] == DiscountValueTypeEnum.PERCENTAGE.value
    assert discount_data["amount_value"] == str(unit_discount.amount)

    assert discount_data["old_value"] == str(line_discount_value_before_update)
    assert discount_data["old_value_type"] == DiscountValueTypeEnum.FIXED.value
    assert discount_data["old_amount_value"] == str(line_discount_amount_before_update)


def test_update_order_line_discount_order_is_not_draft(
    draft_order_with_fixed_discount_order, staff_api_client, permission_manage_orders
):
    draft_order_with_fixed_discount_order.status = OrderStatus.UNFULFILLED
    draft_order_with_fixed_discount_order.save()

    line_to_discount = draft_order_with_fixed_discount_order.lines.first()

    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line_to_discount.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.FIXED.name,
            "value": Decimal("5"),
            "reason": "New reason for unit discount",
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountUpdate"]

    line_to_discount.refresh_from_db()

    errors = data["orderErrors"]
    assert len(errors) == 1

    error = data["orderErrors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == OrderErrorCode.CANNOT_DISCOUNT.name

    assert line_to_discount.unit_discount_amount == Decimal("0")


ORDER_LINE_DISCOUNT_REMOVE = """
mutation OrderLineDiscountRemove($orderLineId: ID!){
  orderLineDiscountRemove(orderLineId: $orderLineId){
    orderLine{
      id
    }
    orderErrors{
      field
      message
      code
    }
  }
}
"""


@patch("saleor.plugins.manager.PluginsManager.calculate_order_line_unit")
def test_delete_discount_from_order_line(
    mocked_calculate_order_line_unit,
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_manage_orders,
):
    line = draft_order_with_fixed_discount_order.lines.first()

    line_undiscounted_price = line.undiscounted_unit_price

    mocked_calculate_order_line_unit.return_value = line_undiscounted_price

    line.unit_discount_amount = Decimal("2.5")
    line.unit_discount_type = DiscountValueType.FIXED
    line.unit_discount_value = Decimal("2.5")
    line.save()

    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line.pk),
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_REMOVE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountRemove"]

    errors = data["orderErrors"]
    assert len(errors) == 0

    line.refresh_from_db()

    assert line.unit_price == line_undiscounted_price
    unit_discount = line.unit_discount
    currency = draft_order_with_fixed_discount_order.currency
    assert unit_discount == Money(Decimal(0), currency=currency)

    event = draft_order_with_fixed_discount_order.events.get()
    assert event.type == OrderEvents.ORDER_LINE_DISCOUNT_REMOVED
    parameters = event.parameters
    lines = parameters.get("lines", {})
    assert len(lines) == 1

    line_data = lines[0]
    assert line_data.get("line_pk") == line.pk


def test_delete_order_line_discount_order_is_not_draft(
    draft_order_with_fixed_discount_order, staff_api_client, permission_manage_orders
):
    draft_order_with_fixed_discount_order.status = OrderStatus.UNFULFILLED
    draft_order_with_fixed_discount_order.save()

    line = draft_order_with_fixed_discount_order.lines.first()

    line.unit_discount_amount = Decimal("2.5")
    line.unit_discount_type = DiscountValueType.FIXED
    line.unit_discount_value = Decimal("2.5")
    line.save()

    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line.pk),
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_REMOVE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountRemove"]

    errors = data["orderErrors"]
    assert len(errors) == 1

    assert draft_order_with_fixed_discount_order.discounts.get()

    error = data["orderErrors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == OrderErrorCode.CANNOT_DISCOUNT.name

    assert line.unit_discount_amount == Decimal("2.5")
