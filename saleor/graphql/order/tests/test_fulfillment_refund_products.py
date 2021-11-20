from decimal import Decimal
from unittest.mock import ANY, patch

import graphene
import pytest
from prices import Money, TaxedMoney

from ....core.prices import quantize_price
from ....order import OrderEvents
from ....order.error_codes import OrderErrorCode
from ....order.interface import OrderPaymentAction
from ....order.models import FulfillmentLine, FulfillmentStatus, OrderEvent
from ....payment import ChargeStatus, PaymentError, TransactionKind
from ....warehouse.models import Allocation, Stock
from ...tests.utils import get_graphql_content

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
            payments
            orderLines
        }
    }
}
"""


@patch("saleor.payment.gateway.refund")
@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_fulfillment_refund_products_with_back_in_stock_webhook(
    back_in_stock_webhook_trigger,
    mock_refunded,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    payment_dummy,
    mock_refund_response,
):
    mock_refund_response(mock_refunded)
    Allocation.objects.update(quantity_allocated=5)
    payment_dummy.total = order_with_lines.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    line_to_refund = order_with_lines.lines.first()
    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_refund.pk)
    variables = {
        "order": order_id,
        "input": {"orderLines": [{"orderLineId": line_id, "quantity": 1}]},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["errors"]
    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    back_in_stock_webhook_trigger.assert_called_once_with(Stock.objects.first())


def test_fulfillment_refund_gift_card_products(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    payment_dummy,
):
    # given
    Allocation.objects.update(quantity_allocated=5)
    payment_dummy.total = order_with_lines.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    line_to_refund = order_with_lines.lines.first()

    line_to_refund.is_gift_card = True
    line_to_refund.save(update_fields=["is_gift_card"])

    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_refund.pk)
    variables = {
        "order": order_id,
        "input": {"orderLines": [{"orderLineId": line_id, "quantity": 1}]},
    }

    # when
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # then
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["errors"]
    assert not refund_fulfillment
    assert len(errors) == 1
    assert errors[0]["field"] == "amountToRefund"
    assert errors[0]["code"] == OrderErrorCode.GIFT_CARD_LINE.name


def test_fulfillment_refund_products_order_without_payment(
    staff_api_client, permission_manage_orders, fulfilled_order
):
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    variables = {"order": order_id, "input": {"amountToRefund": "11.00"}}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    fulfillment = data["fulfillment"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "order"
    assert errors[0]["code"] == OrderErrorCode.CANNOT_REFUND.name
    assert fulfillment is None


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_amount_and_shipping_costs(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    payment_dummy,
):
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    amount_to_refund = Decimal("11.00")
    variables = {
        "order": order_id,
        "input": {"amountToRefund": amount_to_refund, "includeShippingCosts": True},
    }

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        amount=quantize_price(
            amount_to_refund,
            fulfilled_order.currency,
        ),
        channel_slug=fulfilled_order.channel.slug,
    )


def test_fulfillment_refund_products_amount_costs_for_order_with_gift_card_lines(
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    payment_dummy,
):
    # given
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)

    line = fulfilled_order.lines.first()
    line.is_gift_card = True
    line.save(update_fields=["is_gift_card"])

    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    amount_to_refund = Decimal("11.00")
    variables = {
        "order": order_id,
        "input": {"amountToRefund": amount_to_refund, "includeShippingCosts": True},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.CANNOT_REFUND.name
    assert errors[0]["field"] == "amountToRefund"


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_refund_raising_payment_error(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    payment_dummy,
):
    # given
    mocked_refund.side_effect = PaymentError("Error")

    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    amount_to_refund = Decimal("11.00")
    variables = {
        "order": order_id,
        "input": {"amountToRefund": amount_to_refund, "includeShippingCosts": True},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]

    # then
    assert data["fulfillment"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "payments"
    assert data["errors"][0]["code"] == OrderErrorCode.CANNOT_REFUND.name

    event = OrderEvent.objects.filter(type=OrderEvents.PAYMENT_REFUND_FAILED).get()
    assert event.parameters["payment_id"] == payment_dummy.token


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_order_lines(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    payment_dummy,
    mock_refund_response,
):
    mock_refund_response(mocked_refund)
    payment_dummy.total = order_with_lines.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    line_to_refund = order_with_lines.lines.first()
    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_refund.pk)
    variables = {
        "order": order_id,
        "input": {"orderLines": [{"orderLineId": line_id, "quantity": 2}]},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["errors"]
    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    assert len(refund_fulfillment["lines"]) == 1
    assert refund_fulfillment["lines"][0]["orderLine"]["id"] == line_id
    assert refund_fulfillment["lines"][0]["quantity"] == 2

    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        amount=line_to_refund.unit_price_gross_amount * 2,
        channel_slug=order_with_lines.channel.slug,
    )


def test_fulfillment_refund_products_order_lines_quantity_bigger_than_total(
    staff_api_client, permission_manage_orders, order_with_lines, payment_dummy
):
    payment_dummy.total = order_with_lines.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    line_to_refund = order_with_lines.lines.first()
    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_refund.pk)
    variables = {
        "order": order_id,
        "input": {"orderLines": [{"orderLineId": line_id, "quantity": 200}]},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "orderLineId"
    assert errors[0]["code"] == OrderErrorCode.INVALID_QUANTITY.name
    assert refund_fulfillment is None


def test_fulfillment_refund_products_order_lines_quantity_bigger_than_unfulfilled(
    staff_api_client, permission_manage_orders, order_with_lines, payment_dummy
):
    payment_dummy.total = order_with_lines.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    line_to_refund = order_with_lines.lines.first()
    line_to_refund.quantity = 3
    line_to_refund.quantity_fulfilled = 3
    line_to_refund.save()
    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_refund.pk)
    variables = {
        "order": order_id,
        "input": {"orderLines": [{"orderLineId": line_id, "quantity": 1}]},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "orderLineId"
    assert errors[0]["code"] == OrderErrorCode.INVALID_QUANTITY.name
    assert refund_fulfillment is None


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_fulfillment_lines(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    payment_dummy,
    mock_refund_response,
):
    mock_refund_response(mocked_refund)
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    fulfillment_line_to_refund = fulfilled_order.fulfillments.first().lines.first()
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_refund.pk
    )
    order_line_id = graphene.Node.to_global_id(
        "OrderLine", fulfillment_line_to_refund.order_line.pk
    )
    variables = {
        "order": order_id,
        "input": {
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 2}
            ]
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["errors"]

    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    assert len(refund_fulfillment["lines"]) == 1
    assert refund_fulfillment["lines"][0]["orderLine"]["id"] == order_line_id
    assert refund_fulfillment["lines"][0]["quantity"] == 2

    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        channel_slug=fulfilled_order.channel.slug,
        amount=fulfillment_line_to_refund.order_line.unit_price_gross_amount * 2,
    )


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_waiting_fulfillment_lines(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    payment_dummy,
    mock_refund_response,
):
    mock_refund_response(mocked_refund)
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])
    fulfilled_order.payments.add(payment_dummy)
    fulfillment_line_to_refund = fulfilled_order.fulfillments.first().lines.first()
    fulfillment_line_to_refund.order_line.quantity_fulfilled = 0
    fulfillment_line_to_refund.order_line.save(update_fields=["quantity_fulfilled"])
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_refund.pk
    )
    order_line_id = graphene.Node.to_global_id(
        "OrderLine", fulfillment_line_to_refund.order_line.pk
    )
    variables = {
        "order": order_id,
        "input": {
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 3}
            ]
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["errors"]
    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    assert len(refund_fulfillment["lines"]) == 1
    assert refund_fulfillment["lines"][0]["orderLine"]["id"] == order_line_id
    assert refund_fulfillment["lines"][0]["quantity"] == 3
    assert not FulfillmentLine.objects.filter(pk=fulfillment_line_to_refund.pk).exists()
    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        amount=fulfillment_line_to_refund.order_line.unit_price_gross_amount * 3,
        channel_slug=fulfilled_order.channel.slug,
    )


def test_fulfillment_refund_products_gift_card_fulfillment_line(
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    payment_dummy,
):
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    fulfillment_line_to_refund = fulfilled_order.fulfillments.first().lines.first()

    order_line = fulfillment_line_to_refund.order_line
    order_line.is_gift_card = True
    order_line.save(update_fields=["is_gift_card"])

    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_refund.pk
    )
    variables = {
        "order": order_id,
        "input": {
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 2}
            ]
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["errors"]
    assert not refund_fulfillment
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.GIFT_CARD_LINE.name
    assert errors[0]["field"] == "amountToRefund"


def test_fulfillment_refund_products_fulfillment_lines_quantity_bigger_than_total(
    staff_api_client, permission_manage_orders, fulfilled_order, payment_dummy
):
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    fulfillment_line_to_refund = fulfilled_order.fulfillments.first().lines.first()
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_refund.pk
    )
    variables = {
        "order": order_id,
        "input": {
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 200}
            ]
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "fulfillmentLineId"
    assert errors[0]["code"] == OrderErrorCode.INVALID_QUANTITY.name
    assert refund_fulfillment is None


def test_fulfillment_refund_products_amount_bigger_than_captured_amount(
    staff_api_client, permission_manage_orders, fulfilled_order, payment_dummy
):
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    fulfillment_line_to_refund = fulfilled_order.fulfillments.first().lines.first()
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_refund.pk
    )
    variables = {
        "order": order_id,
        "input": {
            "amountToRefund": "1000.00",
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 2}
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "amountToRefund"
    assert errors[0]["code"] == OrderErrorCode.CANNOT_REFUND.name
    assert refund_fulfillment is None


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_fulfillment_lines_include_shipping_costs(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    payment_dummy,
    mock_refund_response,
):
    mock_refund_response(mocked_refund)
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    fulfillment_line_to_refund = fulfilled_order.fulfillments.first().lines.first()
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_refund.pk
    )
    order_line_id = graphene.Node.to_global_id(
        "OrderLine", fulfillment_line_to_refund.order_line.pk
    )
    variables = {
        "order": order_id,
        "input": {
            "includeShippingCosts": True,
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 2}
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["errors"]

    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    assert len(refund_fulfillment["lines"]) == 1
    assert refund_fulfillment["lines"][0]["orderLine"]["id"] == order_line_id
    assert refund_fulfillment["lines"][0]["quantity"] == 2
    amount = fulfillment_line_to_refund.order_line.unit_price_gross_amount * 2
    amount += fulfilled_order.shipping_price_gross_amount

    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        amount=amount,
        channel_slug=fulfilled_order.channel.slug,
    )


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_order_lines_include_shipping_costs(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    payment_dummy,
    mock_refund_response,
):
    mock_refund_response(mocked_refund)
    payment_dummy.total = order_with_lines.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    line_to_refund = order_with_lines.lines.first()
    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_refund.pk)
    variables = {
        "order": order_id,
        "input": {
            "includeShippingCosts": True,
            "orderLines": [{"orderLineId": line_id, "quantity": 2}],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["errors"]
    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    assert len(refund_fulfillment["lines"]) == 1
    assert refund_fulfillment["lines"][0]["orderLine"]["id"] == line_id
    assert refund_fulfillment["lines"][0]["quantity"] == 2
    amount = line_to_refund.unit_price_gross_amount * 2
    amount += order_with_lines.shipping_price_gross_amount

    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        amount=amount,
        channel_slug=order_with_lines.channel.slug,
    )


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_fulfillment_lines_custom_amount(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    payment_dummy,
    mock_refund_response,
):
    mock_refund_response(mocked_refund)
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    amount_to_refund = Decimal("10.99")
    fulfillment_line_to_refund = fulfilled_order.fulfillments.first().lines.first()
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_refund.pk
    )
    order_line_id = graphene.Node.to_global_id(
        "OrderLine", fulfillment_line_to_refund.order_line.pk
    )
    variables = {
        "order": order_id,
        "input": {
            "amountToRefund": amount_to_refund,
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 2}
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["errors"]

    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    assert len(refund_fulfillment["lines"]) == 1
    assert refund_fulfillment["lines"][0]["orderLine"]["id"] == order_line_id
    assert refund_fulfillment["lines"][0]["quantity"] == 2

    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        channel_slug=fulfilled_order.channel.slug,
        amount=amount_to_refund,
    )


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_order_lines_custom_amount(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    payment_dummy,
    mock_refund_response,
):
    mock_refund_response(mocked_refund)
    payment_dummy.total = order_with_lines.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    amount_to_refund = Decimal("10.99")
    line_to_refund = order_with_lines.lines.first()
    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_refund.pk)
    variables = {
        "order": order_id,
        "input": {
            "amountToRefund": amount_to_refund,
            "orderLines": [{"orderLineId": line_id, "quantity": 2}],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["errors"]
    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    assert len(refund_fulfillment["lines"]) == 1
    assert refund_fulfillment["lines"][0]["orderLine"]["id"] == line_id
    assert refund_fulfillment["lines"][0]["quantity"] == 2

    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        channel_slug=order_with_lines.channel.slug,
        amount=amount_to_refund,
    )


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_fulfillment_lines_and_order_lines(
    mocked_refund,
    warehouse,
    variant,
    channel_USD,
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    payment_dummy,
    mock_refund_response,
):
    mock_refund_response(mocked_refund)
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    stock = Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=5
    )
    channel_listing = variant.channel_listings.get()
    net = variant.get_price(variant.product, [], channel_USD, channel_listing)
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    variant.track_inventory = False
    variant.save()
    unit_price = TaxedMoney(net=net, gross=gross)
    quantity = 5
    order_line = fulfilled_order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        quantity_fulfilled=2,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        tax_rate=Decimal("0.23"),
    )
    fulfillment = fulfilled_order.fulfillments.get()
    fulfillment.lines.create(order_line=order_line, quantity=2, stock=stock)
    fulfillment_line_to_refund = fulfilled_order.fulfillments.first().lines.first()
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_refund.pk
    )
    order_line_from_fulfillment_line = graphene.Node.to_global_id(
        "OrderLine", fulfillment_line_to_refund.order_line.pk
    )
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)
    variables = {
        "order": order_id,
        "input": {
            "orderLines": [{"orderLineId": order_line_id, "quantity": 2}],
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 2}
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)

    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["errors"]

    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    assert len(refund_fulfillment["lines"]) == 2
    assert refund_fulfillment["lines"][0]["orderLine"]["id"] in [
        order_line_id,
        order_line_from_fulfillment_line,
    ]
    assert refund_fulfillment["lines"][0]["quantity"] == 2

    assert refund_fulfillment["lines"][1]["orderLine"]["id"] in [
        order_line_id,
        order_line_from_fulfillment_line,
    ]
    assert refund_fulfillment["lines"][1]["quantity"] == 2
    amount = fulfillment_line_to_refund.order_line.unit_price_gross_amount * 2
    amount += order_line.unit_price_gross_amount * 2
    amount = quantize_price(amount, fulfilled_order.currency)

    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        channel_slug=fulfilled_order.channel.slug,
        amount=amount,
    )


def test_fulfillment_refund_products_raises_error_if_payment_doesnt_belong_to_order(
    staff_api_client,
    fulfilled_order,
    payment_dummy_factory,
    permission_manage_orders,
):
    # given
    payment_1 = payment_dummy_factory()
    payment_1.captured_amount = payment_1.total
    payment_1.charge_status = ChargeStatus.FULLY_CHARGED
    payment_1.save()
    payment_2 = payment_dummy_factory()
    payment_2.captured_amount = payment_2.total
    payment_2.charge_status = ChargeStatus.FULLY_CHARGED
    payment_2.save()
    payment_1.transactions.create(
        amount=payment_1.captured_amount,
        currency=payment_1.currency,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )
    payment_2.transactions.create(
        amount=payment_2.captured_amount,
        currency=payment_2.currency,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )
    # Only one payments is realted to the order
    fulfilled_order.payments.set([payment_1])

    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    variables = {
        "order": order_id,
        "input": {
            "paymentsToRefund": [
                {
                    "paymentId": graphene.Node.to_global_id("Payment", payment_1.id),
                    "amount": payment_1.captured_amount,
                },
                {
                    "paymentId": graphene.Node.to_global_id("Payment", payment_2.id),
                    "amount": payment_2.captured_amount,
                },
            ],
            "includeShippingCosts": False,
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]

    # then
    assert data["fulfillment"] is None
    assert data["errors"][0]["field"] == "paymentsToRefund"
    assert (
        data["errors"][0]["code"] == OrderErrorCode.PAYMENTS_DO_NOT_BELONG_TO_ORDER.name
    )
    message = "These payments do not belong to the order."
    assert data["errors"][0]["message"] == message
    assert data["errors"][0]["payments"] == [
        graphene.Node.to_global_id("Payment", payment_2.id)
    ]


def test_fulfillment_refund_products_with_amount_to_refund_with_multiple_payments(
    staff_api_client,
    fulfilled_order,
    payment_dummy_factory,
    permission_manage_orders,
):
    # given
    payment_1 = payment_dummy_factory()
    payment_1.captured_amount = payment_1.total
    payment_1.charge_status = ChargeStatus.FULLY_CHARGED
    payment_1.save()
    payment_2 = payment_dummy_factory()
    payment_2.captured_amount = payment_2.total
    payment_2.charge_status = ChargeStatus.FULLY_CHARGED
    payment_2.save()
    payment_1.transactions.create(
        amount=payment_1.captured_amount,
        currency=payment_1.currency,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )
    payment_2.transactions.create(
        amount=payment_2.captured_amount,
        currency=payment_2.currency,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )

    payments = [payment_1, payment_2]

    fulfilled_order.payments.set(payments)

    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    variables = {"order": order_id, "input": {"amountToRefund": "11.00"}}

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]

    # then
    assert data["fulfillment"] is None
    assert data["errors"][0]["field"] == "amountToRefund"
    assert data["errors"][0]["code"] == OrderErrorCode.ORDER_HAS_MULTIPLE_PAYMENTS.name
    message = (
        "It is not possible to use the amount field "
        "for orders with multiple payments."
    )
    assert data["errors"][0]["message"] == message


def test_fulfillment_refund_products_with_amount_to_refund_with_one_payment(
    staff_api_client,
    fulfilled_order,
    payment_dummy_factory,
    permission_manage_orders,
):
    # given
    payment_1 = payment_dummy_factory()
    payment_1.captured_amount = payment_1.total
    payment_1.charge_status = ChargeStatus.FULLY_CHARGED
    payment_1.save()

    payment_1.transactions.create(
        amount=payment_1.captured_amount,
        currency=payment_1.currency,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )

    payments = [payment_1]

    fulfilled_order.payments.set(payments)

    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    variables = {"order": order_id, "input": {"amountToRefund": "11.00"}}

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]

    # then
    assert data["errors"] == []
    assert data["fulfillment"] is not None


def test_fulfillment_refund_products_counts_only_active_payments(
    staff_api_client,
    fulfilled_order,
    payment_dummy_factory,
    permission_manage_orders,
):
    # given
    payment_1 = payment_dummy_factory()
    payment_1.captured_amount = payment_1.total
    payment_1.charge_status = ChargeStatus.FULLY_CHARGED
    payment_1.save()
    payment_2 = payment_dummy_factory()
    payment_2.captured_amount = payment_2.total
    payment_2.charge_status = ChargeStatus.FULLY_CHARGED
    payment_2.is_active = False
    payment_2.save()
    payment_1.transactions.create(
        amount=payment_1.captured_amount,
        currency=payment_1.currency,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )
    payment_2.transactions.create(
        amount=payment_2.captured_amount,
        currency=payment_2.currency,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )

    payments = [payment_1, payment_2]

    fulfilled_order.payments.set(payments)

    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    variables = {"order": order_id, "input": {"amountToRefund": "11.00"}}

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]

    # then
    assert data["errors"] == []
    assert data["fulfillment"] is not None


def test_fulfillment_refund_products_with_payments_to_refund_passed(
    staff_api_client,
    fulfilled_order,
    payment_dummy_factory,
    permission_manage_orders,
):
    # given
    payment_1 = payment_dummy_factory()
    payment_1.captured_amount = payment_1.total
    payment_1.charge_status = ChargeStatus.FULLY_CHARGED
    payment_1.save()
    payment_2 = payment_dummy_factory()
    payment_2.captured_amount = payment_2.total
    payment_2.charge_status = ChargeStatus.FULLY_CHARGED
    payment_2.save()
    payment_1.transactions.create(
        amount=payment_1.captured_amount,
        currency=payment_1.currency,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )
    payment_2.transactions.create(
        amount=payment_2.captured_amount,
        currency=payment_2.currency,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )

    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    variables = {
        "order": order_id,
        "input": {
            "includeShippingCosts": True,
            "paymentsToRefund": [
                {
                    "paymentId": graphene.Node.to_global_id("Payment", payment_1.id),
                    "amount": payment_1.captured_amount,
                },
                {
                    "paymentId": graphene.Node.to_global_id("Payment", payment_2.id),
                },
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    fulfillment = fulfilled_order.fulfillments.filter(
        status=FulfillmentStatus.REFUNDED
    ).get()
    shipping_refund_amount = fulfilled_order.shipping_price_gross_amount
    total_refund_amount = payment_1.captured_amount + shipping_refund_amount

    # then
    assert data["errors"] == []
    assert data["fulfillment"]["id"] == graphene.Node.to_global_id(
        "Fulfillment", fulfillment.id
    )
    assert fulfillment.shipping_refund_amount == shipping_refund_amount
    assert fulfillment.total_refund_amount == total_refund_amount


@pytest.mark.parametrize(
    "ordering", [(1, 2, 3), (1, 3, 2), (3, 2, 1), (3, 1, 2), (2, 1, 3), (2, 3, 1)]
)
@patch("saleor.graphql.order.mutations.fulfillments.create_refund_fulfillment")
def test_fulfillment_refund_products_preserves_payments_order(
    mock_create_refund_fulfillment,
    ordering,
    staff_api_client,
    fulfilled_order,
    payment_dummy_factory,
    permission_manage_orders,
):
    # given
    payment_1 = payment_dummy_factory()
    payment_1.captured_amount = payment_1.total
    payment_1.charge_status = ChargeStatus.FULLY_CHARGED
    payment_1.save()
    payment_2 = payment_dummy_factory()
    payment_2.captured_amount = payment_2.total
    payment_2.charge_status = ChargeStatus.FULLY_CHARGED
    payment_2.save()
    payment_3 = payment_dummy_factory()
    payment_3.captured_amount = payment_2.total
    payment_3.charge_status = ChargeStatus.FULLY_CHARGED
    payment_3.save()

    mapped_payments = {
        "payment_1": payment_1,
        "payment_2": payment_2,
        "payment_3": payment_3,
    }

    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    variables = {
        "order": order_id,
        "input": {
            "includeShippingCosts": False,
            "paymentsToRefund": [
                {
                    "paymentId": graphene.Node.to_global_id(
                        "Payment", mapped_payments[f"payment_{ordering[0]}"].id
                    ),
                },
                {
                    "paymentId": graphene.Node.to_global_id(
                        "Payment", mapped_payments[f"payment_{ordering[1]}"].id
                    ),
                },
                {
                    "paymentId": graphene.Node.to_global_id(
                        "Payment", mapped_payments[f"payment_{ordering[2]}"].id
                    ),
                },
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    payments_to_refund = [
        OrderPaymentAction(mapped_payments[f"payment_{ordering[0]}"], Decimal("0")),
        OrderPaymentAction(mapped_payments[f"payment_{ordering[1]}"], Decimal("0")),
        OrderPaymentAction(mapped_payments[f"payment_{ordering[2]}"], Decimal("0")),
    ]

    # then
    mock_create_refund_fulfillment.assert_called_once_with(
        staff_api_client.user,
        None,
        fulfilled_order,
        payments_to_refund,
        [],
        [],
        ANY,
        False,
    )


def test_fulfillment_refund_products_with_amount_to_refund_passed(
    staff_api_client,
    fulfilled_order,
    payment_dummy_factory,
    permission_manage_orders,
):
    # given
    payment_1 = payment_dummy_factory()
    payment_1.captured_amount = payment_1.total
    payment_1.charge_status = ChargeStatus.FULLY_CHARGED
    payment_1.save()

    payment_1.transactions.create(
        amount=payment_1.captured_amount,
        currency=payment_1.currency,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )

    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    variables = {
        "order": order_id,
        "input": {
            "amountToRefund": payment_1.captured_amount,
            "includeShippingCosts": True,
        },
    }

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    fulfillment = fulfilled_order.fulfillments.filter(
        status=FulfillmentStatus.REFUNDED
    ).get()

    # then
    assert data["errors"] == []
    assert data["fulfillment"]["id"] == graphene.Node.to_global_id(
        "Fulfillment", fulfillment.id
    )
    assert fulfillment.shipping_refund_amount is None
    assert fulfillment.total_refund_amount == payment_1.captured_amount


def test_fulfillment_refund_products_exclude_payments_with_zero_amount(
    staff_api_client,
    fulfilled_order,
    payment_dummy_factory,
    permission_manage_orders,
):
    # given
    payment_1 = payment_dummy_factory()
    payment_1.captured_amount = payment_1.total
    payment_1.charge_status = ChargeStatus.FULLY_CHARGED
    payment_1.save()

    payment_2 = payment_dummy_factory()
    payment_2.captured_amount = payment_2.total
    payment_2.charge_status = ChargeStatus.FULLY_CHARGED
    payment_2.save()

    payment_1.transactions.create(
        amount=payment_1.captured_amount,
        currency=payment_1.currency,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )

    payment_2.transactions.create(
        amount=payment_2.captured_amount,
        currency=payment_2.currency,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )

    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)

    amount_to_refund = payment_1.captured_amount // 2
    variables = {
        "order": order_id,
        "input": {
            "includeShippingCosts": False,
            "paymentsToRefund": [
                {
                    "paymentId": graphene.Node.to_global_id("Payment", payment_1.id),
                    "amount": amount_to_refund,
                },
                {
                    "paymentId": graphene.Node.to_global_id("Payment", payment_2.id),
                    "amount": 0,
                },
            ],
        },
    }

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    fulfillment = fulfilled_order.fulfillments.filter(
        status=FulfillmentStatus.REFUNDED
    ).get()

    # then
    assert data["errors"] == []
    assert data["fulfillment"]["id"] == graphene.Node.to_global_id(
        "Fulfillment", fulfillment.id
    )
    assert fulfillment.shipping_refund_amount is None
    assert fulfillment.total_refund_amount == amount_to_refund
