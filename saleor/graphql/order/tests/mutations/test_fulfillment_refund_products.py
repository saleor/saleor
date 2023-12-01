from decimal import Decimal
from unittest import mock
from unittest.mock import ANY, patch

import graphene
from prices import Money, TaxedMoney

from .....core.prices import quantize_price
from .....order import FulfillmentLineData
from .....order.error_codes import OrderErrorCode
from .....order.fetch import OrderLineInfo
from .....order.models import FulfillmentLine, FulfillmentStatus
from .....payment import ChargeStatus, PaymentError
from .....payment.interface import RefundData
from .....tests.utils import flush_post_commit_hooks
from .....warehouse.models import Allocation, Stock
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content

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


def test_fulfillment_refund_products_by_user_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    order_with_lines,
    channel_PLN,
    payment_dummy,
):
    # given
    order_with_lines.channel = channel_PLN
    order_with_lines.save(update_fields=["channel"])

    payment_dummy.total = order_with_lines.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    order_with_lines.payments.add(payment_dummy)

    order_id = to_global_id_or_none(order_with_lines)
    amount_to_refund = Decimal("11.00")
    variables = {
        "order": order_id,
        "input": {"amountToRefund": amount_to_refund, "includeShippingCosts": True},
    }
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)

    # then
    assert_no_permission(response)


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_with_action_requested_by_app(
    mocked_refund,
    app_api_client,
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

    order_id = to_global_id_or_none(fulfilled_order)
    amount_to_refund = Decimal("11.00")
    variables = {
        "order": order_id,
        "input": {"amountToRefund": amount_to_refund, "includeShippingCosts": True},
    }

    # when
    response = app_api_client.post_graphql(
        ORDER_FULFILL_REFUND_MUTATION,
        variables,
        permissions=(permission_manage_orders,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    errors = data["errors"]
    assert not errors

    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        amount=quantize_price(amount_to_refund, fulfilled_order.currency),
        channel_slug=fulfilled_order.channel.slug,
        refund_data=RefundData(
            refund_shipping_costs=True,
            refund_amount_is_automatically_calculated=False,
        ),
    )


@patch("saleor.order.actions.gateway.refund")
@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_fulfillment_refund_products_with_back_in_stock_webhook(
    back_in_stock_webhook_trigger,
    mock_refunded,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    payment_dummy,
):
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    permission_group_manage_orders,
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # then
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["errors"]
    assert not refund_fulfillment
    assert len(errors) == 1
    assert errors[0]["field"] == "orderLineId"
    assert errors[0]["code"] == OrderErrorCode.GIFT_CARD_LINE.name


def test_fulfillment_refund_products_order_without_payment(
    staff_api_client, permission_group_manage_orders, fulfilled_order
):
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    variables = {"order": order_id, "input": {"amountToRefund": "11.00"}}
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    permission_group_manage_orders,
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)

    mocked_refund.assert_called_with(
        payment_dummy,
        ANY,
        amount=quantize_price(amount_to_refund, fulfilled_order.currency),
        channel_slug=fulfilled_order.channel.slug,
        refund_data=RefundData(
            refund_shipping_costs=True,
            refund_amount_is_automatically_calculated=False,
        ),
    )


def test_fulfillment_refund_products_amount_costs_for_order_with_gift_card_lines(
    staff_api_client,
    permission_group_manage_orders,
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)

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
    permission_group_manage_orders,
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.CANNOT_REFUND.name


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_order_lines(
    mocked_refund,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    payment_dummy,
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
        "input": {"orderLines": [{"orderLineId": line_id, "quantity": 2}]},
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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


def test_fulfillment_refund_products_order_lines_quantity_bigger_than_total(
    staff_api_client, permission_group_manage_orders, order_with_lines, payment_dummy
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    staff_api_client, permission_group_manage_orders, order_with_lines, payment_dummy
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    permission_group_manage_orders,
    fulfilled_order,
    payment_dummy,
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
        amount=fulfillment_line_to_refund.order_line.unit_price_gross_amount * 2,
        channel_slug=fulfilled_order.channel.slug,
        refund_data=RefundData(
            fulfillment_lines_to_refund=[
                FulfillmentLineData(
                    line=fulfillment_line_to_refund,
                    quantity=2,
                )
            ],
        ),
    )


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_waiting_fulfillment_lines(
    mocked_refund,
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
    payment_dummy,
):
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
        refund_data=RefundData(
            fulfillment_lines_to_refund=[
                FulfillmentLineData(
                    line=fulfillment_line_to_refund,
                    quantity=3,
                )
            ],
        ),
    )


def test_fulfillment_refund_products_gift_card_fulfillment_line(
    staff_api_client,
    permission_group_manage_orders,
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["errors"]
    errors = data["errors"]
    assert not refund_fulfillment
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.GIFT_CARD_LINE.name
    assert errors[0]["field"] == "fulfillmentLineId"


def test_fulfillment_refund_products_fulfillment_lines_quantity_bigger_than_total(
    staff_api_client, permission_group_manage_orders, fulfilled_order, payment_dummy
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    staff_api_client, permission_group_manage_orders, fulfilled_order, payment_dummy
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    permission_group_manage_orders,
    fulfilled_order,
    payment_dummy,
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
        refund_data=RefundData(
            fulfillment_lines_to_refund=[
                FulfillmentLineData(line=fulfillment_line_to_refund, quantity=2)
            ],
            refund_shipping_costs=True,
        ),
    )


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_order_lines_include_shipping_costs(
    mocked_refund,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    payment_dummy,
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
            "includeShippingCosts": True,
            "orderLines": [{"orderLineId": line_id, "quantity": 2}],
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
        refund_data=RefundData(
            order_lines_to_refund=[
                OrderLineInfo(
                    line=line_to_refund, quantity=2, variant=line_to_refund.variant
                )
            ],
            refund_shipping_costs=True,
        ),
    )


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_fulfillment_lines_custom_amount(
    mocked_refund,
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
    payment_dummy,
):
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
        amount=amount_to_refund,
        channel_slug=fulfilled_order.channel.slug,
        refund_data=RefundData(
            fulfillment_lines_to_refund=[
                FulfillmentLineData(
                    line=fulfillment_line_to_refund,
                    quantity=2,
                )
            ],
            refund_amount_is_automatically_calculated=False,
        ),
    )


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_order_lines_custom_amount(
    mocked_refund,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    payment_dummy,
):
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
        amount=amount_to_refund,
        channel_slug=order_with_lines.channel.slug,
        refund_data=RefundData(
            order_lines_to_refund=[
                OrderLineInfo(
                    line=line_to_refund, quantity=2, variant=line_to_refund.variant
                )
            ],
            refund_amount_is_automatically_calculated=False,
        ),
    )


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_fulfillment_lines_and_order_lines(
    mocked_refund,
    warehouse,
    variant,
    channel_USD,
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
    payment_dummy,
):
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)
    stock = Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=5
    )
    channel_listing = variant.channel_listings.get()
    net = variant.get_price(channel_listing)
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)

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
        amount=amount,
        channel_slug=fulfilled_order.channel.slug,
        refund_data=RefundData(
            order_lines_to_refund=[
                OrderLineInfo(line=order_line, quantity=2, variant=order_line.variant)
            ],
            fulfillment_lines_to_refund=[
                FulfillmentLineData(
                    line=fulfillment_line_to_refund,
                    quantity=2,
                )
            ],
        ),
    )


@patch("saleor.order.actions.order_refunded")
@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_refund_products_calls_order_refunded(
    mocked_refund,
    mocked_order_refunded,
    warehouse,
    variant,
    channel_USD,
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
    payment_dummy,
):
    payment_dummy.total = fulfilled_order.total_gross_amount
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()

    fulfilled_order.payments.add(payment_dummy)
    stock = Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=5
    )
    channel_listing = variant.channel_listings.get()
    net = variant.get_price(channel_listing)
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)

    # then
    flush_post_commit_hooks()
    amount = fulfillment_line_to_refund.order_line.unit_price_gross_amount * 2
    amount += order_line.unit_price_gross_amount * 2
    amount = amount.quantize(Decimal("0.001"))

    mocked_order_refunded.assert_called_once_with(
        order=fulfilled_order,
        user=staff_api_client.user,
        app=None,
        amount=amount,
        payment=payment_dummy,
        manager=mock.ANY,
        trigger_order_updated=False,
    )
