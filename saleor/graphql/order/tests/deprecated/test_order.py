import warnings
from decimal import Decimal
from functools import partial
from unittest.mock import ANY, patch

import graphene
import pytest
from prices import Money, TaxedMoney, fixed_discount

from .....channel.utils import DEPRECATION_WARNING_MESSAGE
from .....core.prices import quantize_price
from .....discount import DiscountValueType
from .....order import OrderEvents, OrderOrigin, OrderStatus
from .....order import events as order_events
from .....order.fetch import OrderLineInfo
from .....order.interface import OrderTaxedPricesData
from .....order.models import FulfillmentStatus, Order, OrderEvent, OrderLine
from .....payment import ChargeStatus
from .....payment.interface import RefundData
from ....core.enums import ReportingPeriod
from ....discount.enums import DiscountValueTypeEnum
from ....tests.utils import get_graphql_content


def assert_proper_webhook_called_once(order, status, draft_mock, order_mock):
    if status == OrderStatus.DRAFT:
        draft_mock.assert_called_once_with(order)
        order_mock.assert_not_called()
    else:
        draft_mock.assert_not_called()
        order_mock.assert_called_once_with(order)


QUERY_ORDER_TOTAL = """
query Orders($period: ReportingPeriod, $channel: String) {
    ordersTotal(period: $period, channel: $channel ) {
        gross {
            amount
            currency
        }
        net {
            currency
            amount
        }
    }
}
"""


def test_orders_total(staff_api_client, permission_manage_orders, order_with_lines):
    # given
    order = order_with_lines
    variables = {"period": ReportingPeriod.TODAY.name}

    # when
    with warnings.catch_warnings(record=True) as warns:
        response = staff_api_client.post_graphql(
            QUERY_ORDER_TOTAL, variables, permissions=[permission_manage_orders]
        )
        content = get_graphql_content(response)

    # then
    amount = str(content["data"]["ordersTotal"]["gross"]["amount"])
    assert Money(amount, "USD") == order.total.gross
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


ORDER_LINE_DELETE_MUTATION = """
    mutation OrderLineDelete($id: ID!) {
        orderLineDelete(id: $id) {
            errors {
                field
                message
            }
            orderLine {
                id
            }
            order {
                id
                total{
                    gross{
                        currency
                        amount
                    }
                }
            }
        }
    }
"""


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_line_remove_by_old_line_id(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
):
    query = ORDER_LINE_DELETE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    line = order.lines.first()
    line.old_id = 1
    line.save(update_fields=["old_id"])

    line_id = graphene.Node.to_global_id("OrderLine", line.old_id)
    variables = {"id": line_id}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderLineDelete"]
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.REMOVED_PRODUCTS
    assert data["orderLine"]["id"] == graphene.Node.to_global_id("OrderLine", line.pk)
    assert line not in order.lines.all()
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )


ORDER_LINE_UPDATE_MUTATION = """
    mutation OrderLineUpdate($lineId: ID!, $quantity: Int!) {
        orderLineUpdate(id: $lineId, input: {quantity: $quantity}) {
            errors {
                field
                message
            }
            orderLine {
                id
                quantity
            }
            order {
                total {
                    gross {
                        amount
                    }
                }
            }
        }
    }
"""


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_line_update_by_old_line_id(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
    staff_user,
):
    # given
    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    line = order.lines.first()
    line.old_id = 1
    line.save(update_fields=["old_id"])

    new_quantity = 1
    removed_quantity = 2
    line_id = graphene.Node.to_global_id("OrderLine", line.old_id)
    variables = {"lineId": line_id, "quantity": new_quantity}
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # Ensure the line has the expected quantity
    assert line.quantity == 3

    # No event should exist yet
    assert not OrderEvent.objects.exists()

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]
    assert data["orderLine"]["quantity"] == new_quantity
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )
    removed_items_event = OrderEvent.objects.last()  # type: OrderEvent
    assert removed_items_event.type == order_events.OrderEvents.REMOVED_PRODUCTS
    assert removed_items_event.user == staff_user
    assert removed_items_event.parameters == {
        "lines": [
            {"quantity": removed_quantity, "line_pk": str(line.pk), "item": str(line)}
        ]
    }


ORDER_FULFILL_QUERY = """
    mutation fulfillOrder(
        $order: ID, $input: OrderFulfillInput!
    ) {
        orderFulfill(
            order: $order,
            input: $input
        ) {
            errors {
                field
                code
                message
                warehouse
                orderLines
            }
        }
    }
"""


@pytest.mark.parametrize("fulfillment_auto_approve", [True, False])
@patch("saleor.graphql.order.mutations.order_fulfill.create_fulfillments")
def test_order_fulfill_old_line_id(
    mock_create_fulfillments,
    fulfillment_auto_approve,
    staff_api_client,
    staff_user,
    order_with_lines,
    permission_manage_orders,
    warehouse,
    site_settings,
):
    site_settings.fulfillment_auto_approve = fulfillment_auto_approve
    site_settings.save(update_fields=["fulfillment_auto_approve"])
    order = order_with_lines
    query = ORDER_FULFILL_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line, order_line2 = order.lines.all()
    order_line.old_id = 1
    order_line2.old_id = 2
    OrderLine.objects.bulk_update([order_line, order_line2], ["old_id"])

    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.old_id)
    order_line2_id = graphene.Node.to_global_id("OrderLine", order_line2.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "order": order_id,
        "input": {
            "notifyCustomer": True,
            "lines": [
                {
                    "orderLineId": order_line_id,
                    "stocks": [{"quantity": 3, "warehouse": warehouse_id}],
                },
                {
                    "orderLineId": order_line2_id,
                    "stocks": [{"quantity": 2, "warehouse": warehouse_id}],
                },
            ],
        },
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderFulfill"]
    assert not data["errors"]

    fulfillment_lines_for_warehouses = {
        warehouse.pk: [
            {"order_line": order_line, "quantity": 3},
            {"order_line": order_line2, "quantity": 2},
        ]
    }
    mock_create_fulfillments.assert_called_once_with(
        staff_user,
        None,
        order,
        fulfillment_lines_for_warehouses,
        ANY,
        site_settings,
        True,
        allow_stock_to_be_exceeded=False,
        approved=fulfillment_auto_approve,
        tracking_number="",
    )


ORDER_FULFILL_REFUND_MUTATION = """
mutation OrderFulfillmentRefundProducts(
    $order: ID!, $input: OrderRefundProductsInput!
) {
    orderFulfillmentRefundProducts(
        order: $order,
        input: $input
    ) {
        fulfillment{
            id
            status
            lines{
                id
                quantity
                orderLine{
                    id
                }
            }
        }
        errors {
            field
            code
            message
            warehouse
            orderLines
        }
    }
}
"""


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_order_lines_by_old_id(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    payment_dummy,
):
    # given
    payment_dummy.total = order_with_lines.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    line_to_refund = order_with_lines.lines.first()
    line_to_refund.old_id = 1
    line_to_refund.save(update_fields=["old_id"])
    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_refund.old_id)
    variables = {
        "order": order_id,
        "input": {"orderLines": [{"orderLineId": line_id, "quantity": 2}]},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["errors"]
    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    assert len(refund_fulfillment["lines"]) == 1
    assert refund_fulfillment["lines"][0]["orderLine"][
        "id"
    ] == graphene.Node.to_global_id("OrderLine", line_to_refund.pk)
    assert refund_fulfillment["lines"][0]["quantity"] == 2
    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        amount=line_to_refund.unit_price_gross_amount * 2,
        channel_slug=order_with_lines.channel.slug,
        refund_data=RefundData(
            order_lines_to_refund=[
                OrderLineInfo(
                    line=line_to_refund,
                    quantity=2,
                    variant=line_to_refund.variant,
                )
            ],
        ),
    )


ORDER_FULFILL_RETURN_MUTATION = """
mutation OrderFulfillmentReturnProducts(
    $order: ID!, $input: OrderReturnProductsInput!
) {
    orderFulfillmentReturnProducts(
        order: $order,
        input: $input
    ) {
        returnFulfillment{
            id
            status
            lines{
                id
                quantity
                orderLine{
                    id
                }
            }
        }
        replaceFulfillment{
            id
            status
            lines{
                id
                quantity
                orderLine{
                    id
                }
            }
        }
        order{
            id
            status
        }
        replaceOrder{
            id
            status
            original
            origin
        }
        errors {
            field
            code
            message
            warehouse
            orderLines
        }
    }
}
"""


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_return_products_order_lines_by_old_line_id(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    payment_dummy,
):
    payment_dummy.total = order_with_lines.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    line_to_return = order_with_lines.lines.first()
    line_to_replace = order_with_lines.lines.last()
    line_to_return.old_id = 10
    line_to_return.save(update_fields=["old_id"])

    line_unfulfilled_quantity = line_to_return.quantity_unfulfilled
    line_quantity_to_return = 2

    line_quantity_to_replace = 1

    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_return.old_id)
    replace_line_id = graphene.Node.to_global_id("OrderLine", line_to_replace.pk)

    variables = {
        "order": order_id,
        "input": {
            "refund": True,
            "includeShippingCosts": True,
            "orderLines": [
                {
                    "orderLineId": line_id,
                    "quantity": line_quantity_to_return,
                    "replace": False,
                },
                {
                    "orderLineId": replace_line_id,
                    "quantity": line_quantity_to_replace,
                    "replace": True,
                },
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    order_with_lines.refresh_from_db()
    order_return_fulfillment = order_with_lines.fulfillments.get(
        status=FulfillmentStatus.REFUNDED_AND_RETURNED
    )
    return_fulfillment_line = order_return_fulfillment.lines.filter(
        order_line_id=line_to_return.pk
    ).first()
    assert return_fulfillment_line
    assert return_fulfillment_line.quantity == line_quantity_to_return

    order_replace_fulfillment = order_with_lines.fulfillments.get(
        status=FulfillmentStatus.REPLACED
    )
    replace_fulfillment_line = order_replace_fulfillment.lines.filter(
        order_line_id=line_to_replace.pk
    ).first()
    assert replace_fulfillment_line
    assert replace_fulfillment_line.quantity == line_quantity_to_replace

    line_to_return.refresh_from_db()
    assert (
        line_to_return.quantity_unfulfilled
        == line_unfulfilled_quantity - line_quantity_to_return
    )

    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    return_fulfillment = data["returnFulfillment"]
    replace_fulfillment = data["replaceFulfillment"]
    replace_order = data["replaceOrder"]
    errors = data["errors"]

    assert not errors
    assert (
        return_fulfillment["status"] == FulfillmentStatus.REFUNDED_AND_RETURNED.upper()
    )
    assert len(return_fulfillment["lines"]) == 1
    assert return_fulfillment["lines"][0]["orderLine"][
        "id"
    ] == graphene.Node.to_global_id("OrderLine", line_to_return.pk)
    assert return_fulfillment["lines"][0]["quantity"] == line_quantity_to_return

    assert replace_fulfillment["status"] == FulfillmentStatus.REPLACED.upper()
    assert len(replace_fulfillment["lines"]) == 1
    assert replace_fulfillment["lines"][0]["orderLine"]["id"] == replace_line_id
    assert replace_fulfillment["lines"][0]["quantity"] == line_quantity_to_replace

    assert replace_order["status"] == OrderStatus.DRAFT.upper()
    assert replace_order["origin"] == OrderOrigin.REISSUE.upper()
    assert replace_order["original"] == order_id
    replace_order = Order.objects.get(status=OrderStatus.DRAFT)
    assert replace_order.lines.count() == 1
    replaced_line = replace_order.lines.get()
    assert replaced_line.variant_id == line_to_replace.variant_id
    assert (
        replaced_line.unit_price_gross_amount == line_to_replace.unit_price_gross_amount
    )
    assert replaced_line.quantity == line_quantity_to_replace

    amount = line_to_return.unit_price_gross_amount * line_quantity_to_return
    amount += order_with_lines.shipping_price_gross_amount
    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        amount=amount,
        channel_slug=order_with_lines.channel.slug,
        refund_data=RefundData(
            order_lines_to_refund=[
                OrderLineInfo(
                    line=line_to_return,
                    quantity=line_quantity_to_return,
                    variant=line_to_return.variant,
                ),
            ],
            refund_shipping_costs=True,
        ),
    )


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
    errors{
      field
      message
      code
    }
  }
}
"""


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
def test_update_order_line_discount_old_id(
    status,
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_manage_orders,
):
    order = draft_order_with_fixed_discount_order
    order.status = status
    order.save(update_fields=["status"])
    line_to_discount = order.lines.first()
    unit_price = Money(Decimal(7.3), currency="USD")
    line_to_discount.base_unit_price = unit_price
    line_to_discount.undiscounted_base_unit_price = unit_price
    line_to_discount.unit_price = TaxedMoney(unit_price, unit_price)
    line_to_discount.undiscounted_unit_price = line_to_discount.unit_price
    total_price = line_to_discount.unit_price * line_to_discount.quantity
    line_to_discount.total_price = total_price
    line_to_discount.undiscounted_total_price = total_price
    line_to_discount.old_id = 1
    line_to_discount.save()

    line_price_before_discount = line_to_discount.unit_price

    value = Decimal("5")
    reason = "New reason for unit discount"
    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line_to_discount.old_id),
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

    errors = data["errors"]
    assert not errors

    discount = partial(
        fixed_discount,
        discount=Money(value, currency=order.currency),
    )
    expected_line_price = discount(line_price_before_discount)

    assert line_to_discount.unit_price == quantize_price(expected_line_price, "USD")
    unit_discount = line_to_discount.unit_discount
    assert unit_discount == (line_price_before_discount - expected_line_price).gross

    event = order.events.get()
    assert event.type == OrderEvents.ORDER_LINE_DISCOUNT_UPDATED
    parameters = event.parameters
    lines = parameters.get("lines", {})
    assert len(lines) == 1

    line_data = lines[0]
    assert line_data.get("line_pk") == str(line_to_discount.pk)
    discount_data = line_data.get("discount")

    assert discount_data["value"] == str(value)
    assert discount_data["value_type"] == DiscountValueTypeEnum.FIXED.value
    assert discount_data["amount_value"] == str(unit_discount.amount)


ORDER_LINE_DISCOUNT_REMOVE = """
mutation OrderLineDiscountRemove($orderLineId: ID!){
  orderLineDiscountRemove(orderLineId: $orderLineId){
    orderLine{
      id
    }
    errors{
      field
      message
      code
    }
  }
}
"""


@patch("saleor.plugins.manager.PluginsManager.calculate_order_line_unit")
@patch("saleor.plugins.manager.PluginsManager.calculate_order_line_total")
def test_delete_discount_from_order_line_by_old_id(
    mocked_calculate_order_line_total,
    mocked_calculate_order_line_unit,
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_manage_orders,
):
    order = draft_order_with_fixed_discount_order
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])
    line = order.lines.first()
    line.old_id = 1

    line.save(update_fields=["old_id"])

    line_undiscounted_price = TaxedMoney(
        line.undiscounted_base_unit_price, line.undiscounted_base_unit_price
    )
    line_undiscounted_total_price = line_undiscounted_price * line.quantity

    mocked_calculate_order_line_unit.return_value = OrderTaxedPricesData(
        undiscounted_price=line_undiscounted_price,
        price_with_discounts=line_undiscounted_price,
    )
    mocked_calculate_order_line_total.return_value = OrderTaxedPricesData(
        undiscounted_price=line_undiscounted_total_price,
        price_with_discounts=line_undiscounted_total_price,
    )

    line.unit_discount_amount = Decimal("2.5")
    line.unit_discount_type = DiscountValueType.FIXED
    line.unit_discount_value = Decimal("2.5")
    line.save()

    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line.old_id),
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_REMOVE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountRemove"]

    errors = data["errors"]
    assert len(errors) == 0

    line.refresh_from_db()

    assert line.unit_price == line_undiscounted_price
    assert line.total_price == line_undiscounted_total_price
    unit_discount = line.unit_discount
    currency = order.currency
    assert unit_discount == Money(Decimal(0), currency=currency)

    event = order.events.get()
    assert event.type == OrderEvents.ORDER_LINE_DISCOUNT_REMOVED
    parameters = event.parameters
    lines = parameters.get("lines", {})
    assert len(lines) == 1

    line_data = lines[0]
    assert line_data.get("line_pk") == str(line.pk)
