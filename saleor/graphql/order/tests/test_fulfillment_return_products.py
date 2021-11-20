from decimal import Decimal
from unittest.mock import ANY, patch

import graphene
import pytest
from prices import Money, TaxedMoney

from ....core.prices import quantize_price
from ....order import OrderEvents, OrderOrigin, OrderStatus
from ....order.error_codes import OrderErrorCode
from ....order.interface import OrderPaymentAction
from ....order.models import FulfillmentStatus, Order, OrderEvent
from ....payment import ChargeStatus, PaymentError, TransactionKind
from ....warehouse.models import Stock
from ...tests.utils import get_graphql_content

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


def test_fulfillment_return_products_order_without_payment(
    staff_api_client, permission_manage_orders, fulfilled_order
):
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    variables = {
        "order": order_id,
        "input": {"refund": True, "amountToRefund": "11.00"},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    fulfillment = data["returnFulfillment"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "order"
    assert errors[0]["code"] == OrderErrorCode.CANNOT_REFUND.name
    assert fulfillment is None


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_return_products_amount_and_shipping_costs(
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
        "input": {
            "refund": True,
            "amountToRefund": amount_to_refund,
            "includeShippingCosts": True,
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        channel_slug=fulfilled_order.channel.slug,
        amount=quantize_price(amount_to_refund, fulfilled_order.currency),
    )


def test_fulfillment_return_products_amount_order_with_gift_card(
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
        "input": {
            "refund": True,
            "amountToRefund": amount_to_refund,
            "includeShippingCosts": True,
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    fulfillment = data["returnFulfillment"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "amountToRefund"
    assert errors[0]["code"] == OrderErrorCode.GIFT_CARD_LINE.name
    assert fulfillment is None


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_return_products_refund_raising_payment_error(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    payment_dummy,
):
    mocked_refund.side_effect = PaymentError("Error")

    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    amount_to_refund = Decimal("11.00")
    variables = {
        "order": order_id,
        "input": {
            "refund": True,
            "amountToRefund": amount_to_refund,
            "includeShippingCosts": True,
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    assert data["returnFulfillment"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "payments"
    assert data["errors"][0]["code"] == OrderErrorCode.CANNOT_REFUND.name

    event = OrderEvent.objects.filter(type=OrderEvents.PAYMENT_REFUND_FAILED).get()
    assert event.parameters["payment_id"] == payment_dummy.token


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_return_products_order_lines(
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
    line_to_return = order_with_lines.lines.first()
    line_unfulfilled_quantity = line_to_return.quantity_unfulfilled
    line_quantity_to_return = 2

    line_to_replace = order_with_lines.lines.last()
    line_quantity_to_replace = 1

    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_return.pk)
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
    assert return_fulfillment["lines"][0]["orderLine"]["id"] == line_id
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
        channel_slug=order_with_lines.channel.slug,
        amount=amount,
    )


def test_fulfillment_return_products_gift_card_order_line(
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
    line_to_return = order_with_lines.lines.first()
    line_to_return.is_gift_card = True
    line_to_return.save(update_fields=["is_gift_card"])
    line_quantity_to_return = 2

    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_return.pk)

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
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    fulfillment = data["returnFulfillment"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "amountToRefund"
    assert errors[0]["code"] == OrderErrorCode.GIFT_CARD_LINE.name
    assert fulfillment is None


def test_fulfillment_return_products_order_lines_quantity_bigger_than_total(
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
        "input": {
            "orderLines": [{"orderLineId": line_id, "quantity": 200, "replace": False}]
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    return_fulfillment = data["returnFulfillment"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "orderLineId"
    assert errors[0]["code"] == OrderErrorCode.INVALID_QUANTITY.name
    assert return_fulfillment is None


def test_fulfillment_return_products_order_lines_quantity_bigger_than_unfulfilled(
    staff_api_client, permission_manage_orders, order_with_lines, payment_dummy
):
    payment_dummy.total = order_with_lines.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)
    line_to_return = order_with_lines.lines.first()
    line_to_return.quantity = 3
    line_to_return.quantity_fulfilled = 3
    line_to_return.save()
    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_return.pk)
    variables = {
        "order": order_id,
        "input": {"orderLines": [{"orderLineId": line_id, "quantity": 1}]},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    return_fulfillment = data["returnFulfillment"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "orderLineId"
    assert errors[0]["code"] == OrderErrorCode.INVALID_QUANTITY.name
    assert return_fulfillment is None


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_return_products_order_lines_custom_amount(
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
    line_to_return = order_with_lines.lines.first()
    order_id = graphene.Node.to_global_id("Order", order_with_lines.pk)
    line_id = graphene.Node.to_global_id("OrderLine", line_to_return.pk)
    variables = {
        "order": order_id,
        "input": {
            "refund": True,
            "amountToRefund": amount_to_refund,
            "orderLines": [{"orderLineId": line_id, "quantity": 2, "replace": False}],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    return_fulfillment = data["returnFulfillment"]
    errors = data["errors"]
    assert not errors
    assert (
        return_fulfillment["status"] == FulfillmentStatus.REFUNDED_AND_RETURNED.upper()
    )
    assert len(return_fulfillment["lines"]) == 1
    assert return_fulfillment["lines"][0]["orderLine"]["id"] == line_id
    assert return_fulfillment["lines"][0]["quantity"] == 2

    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        channel_slug=order_with_lines.channel.slug,
        amount=amount_to_refund,
    )


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_return_products_fulfillment_lines(
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
    order_fulfillment = fulfilled_order.fulfillments.first()
    fulfillment_line_to_return = order_fulfillment.lines.first()
    original_fulfillment_line_quantity = fulfillment_line_to_return.quantity
    quantity_to_return = 2

    fulfillment_line_to_replace = order_fulfillment.lines.last()
    quantity_to_replace = 1

    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_return.pk
    )
    fulfillment_line_to_replace_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_replace.pk
    )
    order_line_id = graphene.Node.to_global_id(
        "OrderLine", fulfillment_line_to_return.order_line.pk
    )

    variables = {
        "order": order_id,
        "input": {
            "refund": True,
            "includeShippingCosts": True,
            "fulfillmentLines": [
                {
                    "fulfillmentLineId": fulfillment_line_id,
                    "quantity": quantity_to_return,
                    "replace": False,
                },
                {
                    "fulfillmentLineId": fulfillment_line_to_replace_id,
                    "quantity": quantity_to_replace,
                    "replace": True,
                },
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    fulfilled_order.refresh_from_db()
    order_return_fulfillment = fulfilled_order.fulfillments.get(
        status=FulfillmentStatus.REFUNDED_AND_RETURNED
    )
    return_fulfillment_line = order_return_fulfillment.lines.filter(
        order_line_id=fulfillment_line_to_return.order_line_id
    ).first()
    assert return_fulfillment_line
    assert return_fulfillment_line.quantity == quantity_to_return

    order_replace_fulfillment = fulfilled_order.fulfillments.get(
        status=FulfillmentStatus.REPLACED
    )
    replace_fulfillment_line = order_replace_fulfillment.lines.filter(
        order_line_id=fulfillment_line_to_replace.order_line_id
    ).first()
    assert replace_fulfillment_line
    assert replace_fulfillment_line.quantity == quantity_to_replace

    fulfillment_line_to_return.refresh_from_db()
    assert (
        fulfillment_line_to_return.quantity
        == original_fulfillment_line_quantity - quantity_to_return
    )

    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    errors = data["errors"]
    return_fulfillment = data["returnFulfillment"]
    replace_fulfillment = data["replaceFulfillment"]
    replace_order = data["replaceOrder"]

    assert not errors
    assert (
        return_fulfillment["status"] == FulfillmentStatus.REFUNDED_AND_RETURNED.upper()
    )
    assert len(return_fulfillment["lines"]) == 1
    assert return_fulfillment["lines"][0]["orderLine"]["id"] == order_line_id
    assert return_fulfillment["lines"][0]["quantity"] == 2

    assert replace_fulfillment["status"] == FulfillmentStatus.REPLACED.upper()
    assert len(replace_fulfillment["lines"]) == 1
    assert replace_fulfillment["lines"][0]["quantity"] == quantity_to_replace

    assert replace_order["status"] == OrderStatus.DRAFT.upper()
    assert replace_order["origin"] == OrderOrigin.REISSUE.upper()
    assert replace_order["original"] == order_id

    replace_order = Order.objects.get(status=OrderStatus.DRAFT)
    assert replace_order.lines.count() == 1
    replaced_line = replace_order.lines.get()
    assert replaced_line.variant_id == fulfillment_line_to_replace.order_line.variant_id
    assert (
        replaced_line.unit_price_gross_amount
        == fulfillment_line_to_replace.order_line.unit_price_gross_amount
    )
    assert replaced_line.quantity == quantity_to_replace

    amount = (
        fulfillment_line_to_return.order_line.unit_price_gross_amount
        * quantity_to_return
    )
    amount += fulfilled_order.shipping_price_gross_amount

    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        channel_slug=fulfilled_order.channel.slug,
        amount=amount,
    )


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_return_products_gift_card_fulfillment_line(
    mocked_refund,
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    payment_dummy,
):
    # given
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    order_fulfillment = fulfilled_order.fulfillments.first()

    fulfillment_line_to_replace = order_fulfillment.lines.last()
    order_line = fulfillment_line_to_replace.order_line
    order_line.is_gift_card = True
    order_line.save(update_fields=["is_gift_card"])
    quantity_to_replace = 1

    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_to_replace_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_replace.pk
    )

    variables = {
        "order": order_id,
        "input": {
            "refund": True,
            "includeShippingCosts": True,
            "fulfillmentLines": [
                {
                    "fulfillmentLineId": fulfillment_line_to_replace_id,
                    "quantity": quantity_to_replace,
                    "replace": True,
                },
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    fulfillment = data["returnFulfillment"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "amountToRefund"
    assert errors[0]["code"] == OrderErrorCode.GIFT_CARD_LINE.name
    assert fulfillment is None


def test_fulfillment_return_products_fulfillment_lines_quantity_bigger_than_total(
    staff_api_client, permission_manage_orders, fulfilled_order, payment_dummy
):
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    fulfillment_line_to_return = fulfilled_order.fulfillments.first().lines.first()
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_return.pk
    )
    variables = {
        "order": order_id,
        "input": {
            "refund": True,
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 200}
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    return_fulfillment = data["returnFulfillment"]

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "fulfillmentLineId"
    assert errors[0]["code"] == OrderErrorCode.INVALID_QUANTITY.name
    assert return_fulfillment is None


def test_fulfillment_return_products_amount_bigger_than_captured_amount(
    staff_api_client, permission_manage_orders, fulfilled_order, payment_dummy
):
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    fulfillment_line_to_return = fulfilled_order.fulfillments.first().lines.first()
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_return.pk
    )
    variables = {
        "order": order_id,
        "input": {
            "refund": True,
            "amountToRefund": "1000.00",
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 2}
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    return_fulfillment = data["returnFulfillment"]

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "amountToRefund"
    assert errors[0]["code"] == OrderErrorCode.CANNOT_REFUND.name
    assert return_fulfillment is None


def test_fulfillment_return_products_lines_with_incorrect_status(
    staff_api_client, permission_manage_orders, fulfilled_order, payment_dummy
):
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.status = FulfillmentStatus.RETURNED
    fulfillment.save()
    fulfillment_line_to_return = fulfilled_order.fulfillments.first().lines.first()
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_return.pk
    )
    variables = {
        "order": order_id,
        "input": {
            "refund": True,
            "amountToRefund": "1000.00",
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 2}
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    return_fulfillment = data["returnFulfillment"]

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "amountToRefund"
    assert errors[0]["code"] == OrderErrorCode.CANNOT_REFUND.name
    assert return_fulfillment is None


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_return_products_fulfillment_lines_include_shipping_costs(
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
    fulfillment_line_to_return = fulfilled_order.fulfillments.first().lines.first()
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_return.pk
    )
    order_line_id = graphene.Node.to_global_id(
        "OrderLine", fulfillment_line_to_return.order_line.pk
    )
    variables = {
        "order": order_id,
        "input": {
            "refund": True,
            "includeShippingCosts": True,
            "fulfillmentLines": [
                {"fulfillmentLineId": fulfillment_line_id, "quantity": 2}
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    return_fulfillment = data["returnFulfillment"]
    errors = data["errors"]

    assert not errors
    assert (
        return_fulfillment["status"] == FulfillmentStatus.REFUNDED_AND_RETURNED.upper()
    )
    assert len(return_fulfillment["lines"]) == 1
    assert return_fulfillment["lines"][0]["orderLine"]["id"] == order_line_id
    assert return_fulfillment["lines"][0]["quantity"] == 2
    amount = fulfillment_line_to_return.order_line.unit_price_gross_amount * 2
    amount += fulfilled_order.shipping_price_gross_amount

    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        channel_slug=fulfilled_order.channel.slug,
        amount=amount,
    )


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_return_products_fulfillment_lines_and_order_lines(
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
    fulfillment_line_to_replace = fulfilled_order.fulfillments.first().lines.first()
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    fulfillment_line_id = graphene.Node.to_global_id(
        "FulfillmentLine", fulfillment_line_to_replace.pk
    )
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)
    variables = {
        "order": order_id,
        "input": {
            "refund": True,
            "orderLines": [
                {"orderLineId": order_line_id, "quantity": 2, "replace": False}
            ],
            "fulfillmentLines": [
                {
                    "fulfillmentLineId": fulfillment_line_id,
                    "quantity": 1,
                    "replace": True,
                }
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    errors = data["errors"]
    return_fulfillment = data["returnFulfillment"]
    replace_fulfillment = data["replaceFulfillment"]
    replace_order = data["replaceOrder"]

    assert not errors
    assert (
        return_fulfillment["status"] == FulfillmentStatus.REFUNDED_AND_RETURNED.upper()
    )
    assert len(return_fulfillment["lines"]) == 1
    assert return_fulfillment["lines"][0]["orderLine"]["id"] == order_line_id
    assert return_fulfillment["lines"][0]["quantity"] == 2

    assert replace_fulfillment["status"] == FulfillmentStatus.REPLACED.upper()
    assert len(replace_fulfillment["lines"]) == 1
    assert replace_fulfillment["lines"][0]["quantity"] == 1

    assert replace_order["status"] == OrderStatus.DRAFT.upper()
    assert replace_order["origin"] == OrderOrigin.REISSUE.upper()
    assert replace_order["original"] == order_id

    replace_order = Order.objects.get(status=OrderStatus.DRAFT)
    assert replace_order.lines.count() == 1
    replaced_line = replace_order.lines.get()
    assert replaced_line.variant_id == fulfillment_line_to_replace.order_line.variant_id
    assert (
        replaced_line.unit_price_gross_amount
        == fulfillment_line_to_replace.order_line.unit_price_gross_amount
    )
    assert replaced_line.quantity == 1

    amount = order_line.unit_price_gross_amount * 2
    amount = quantize_price(amount, fulfilled_order.currency)

    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        channel_slug=fulfilled_order.channel.slug,
        amount=amount,
    )


def test_fulfillment_refund_products_with_amount_to_refund_with_payments(
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
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]

    # then
    assert data["returnFulfillment"] is None
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
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]

    # then
    assert data["errors"] == []
    assert data["returnFulfillment"] is not None


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
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]

    # then
    assert data["errors"] == []
    assert data["returnFulfillment"] is not None


@pytest.mark.parametrize(
    "ordering", [(1, 2, 3), (1, 3, 2), (3, 2, 1), (3, 1, 2), (2, 1, 3), (2, 3, 1)]
)
@patch(
    "saleor.graphql.order.mutations.fulfillments."
    "create_fulfillments_for_returned_products"
)
def test_fulfillment_return_products_preserves_payments_order(
    mock_create_fulfillments_for_returned_products,
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
            "refund": True,
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
    staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)
    payments_to_refund = [
        OrderPaymentAction(mapped_payments[f"payment_{ordering[0]}"], Decimal("0")),
        OrderPaymentAction(mapped_payments[f"payment_{ordering[1]}"], Decimal("0")),
        OrderPaymentAction(mapped_payments[f"payment_{ordering[2]}"], Decimal("0")),
    ]

    # then
    mock_create_fulfillments_for_returned_products.assert_called_once_with(
        staff_api_client.user,
        None,
        fulfilled_order,
        payments_to_refund,
        [],
        [],
        ANY,
        False,
        True,
    )


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
            "refund": True,
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
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]

    fulfillment = fulfilled_order.fulfillments.filter(
        status=FulfillmentStatus.REFUNDED_AND_RETURNED
    ).get()

    # then
    assert data["errors"] == []
    assert data["returnFulfillment"]["id"] == graphene.Node.to_global_id(
        "Fulfillment", fulfillment.id
    )
    assert fulfillment.shipping_refund_amount is None
    assert fulfillment.total_refund_amount == amount_to_refund
