from decimal import Decimal
from unittest.mock import ANY, patch

import graphene
import pytest
from prices import Money, TaxedMoney

from ....core.prices import quantize_price
from ....order import OrderEvents
from ....order.error_codes import OrderErrorCode
from ....order.models import FulfillmentStatus, OrderEvent
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


@patch("saleor.order.actions.try_refund")
@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_fulfillment_refund_products_with_back_in_stock_webhook(
    back_in_stock_webhook_trigger,
    mock_refunded,
    staff_api_client,
    permission_manage_orders,
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
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]
    refund_fulfillment = data["fulfillment"]
    errors = data["errors"]
    assert not errors
    assert refund_fulfillment["status"] == FulfillmentStatus.REFUNDED.upper()
    back_in_stock_webhook_trigger.assert_called_once_with(Stock.objects.first())


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


@patch("saleor.order.actions.try_refund")
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
        order=fulfilled_order,
        user=staff_api_client.user,
        app=None,
        payment=payment_dummy,
        manager=ANY,
        channel_slug=fulfilled_order.channel.slug,
        amount=quantize_price(
            amount_to_refund,
            fulfilled_order.currency,
        ),
    )


@patch("saleor.payment.actions.gateway.refund")
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
    assert data["fulfillment"]["status"] == FulfillmentStatus.REFUNDED.upper()
    event = OrderEvent.objects.filter(type=OrderEvents.PAYMENT_REFUND_FAILED).get()
    assert event.parameters["payment_id"] == payment_dummy.token


@patch("saleor.order.actions.try_refund")
def test_fulfillment_refund_products_order_lines(
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
        order=order_with_lines,
        user=staff_api_client.user,
        app=None,
        payment=payment_dummy,
        manager=ANY,
        channel_slug=order_with_lines.channel.slug,
        amount=line_to_refund.unit_price_gross_amount * 2,
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


@patch("saleor.order.actions.try_refund")
def test_fulfillment_refund_products_fulfillment_lines(
    mocked_refund,
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
        order=fulfilled_order,
        user=staff_api_client.user,
        app=None,
        payment=payment_dummy,
        manager=ANY,
        channel_slug=fulfilled_order.channel.slug,
        amount=fulfillment_line_to_refund.order_line.unit_price_gross_amount * 2,
    )


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


@patch("saleor.order.actions.try_refund")
def test_fulfillment_refund_products_fulfillment_lines_include_shipping_costs(
    mocked_refund,
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
        order=fulfilled_order,
        user=staff_api_client.user,
        app=None,
        payment=payment_dummy,
        manager=ANY,
        channel_slug=fulfilled_order.channel.slug,
        amount=amount,
    )


@patch("saleor.order.actions.try_refund")
def test_fulfillment_refund_products_order_lines_include_shipping_costs(
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
        order=order_with_lines,
        user=staff_api_client.user,
        app=None,
        payment=payment_dummy,
        manager=ANY,
        channel_slug=order_with_lines.channel.slug,
        amount=amount,
    )


@patch("saleor.order.actions.try_refund")
def test_fulfillment_refund_products_fulfillment_lines_custom_amount(
    mocked_refund,
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
        order=fulfilled_order,
        user=staff_api_client.user,
        app=None,
        payment=payment_dummy,
        manager=ANY,
        channel_slug=fulfilled_order.channel.slug,
        amount=amount_to_refund,
    )


@patch("saleor.order.actions.try_refund")
def test_fulfillment_refund_products_order_lines_custom_amount(
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
        order=order_with_lines,
        user=staff_api_client.user,
        app=None,
        payment=payment_dummy,
        manager=ANY,
        channel_slug=order_with_lines.channel.slug,
        amount=amount_to_refund,
    )


@patch("saleor.order.actions.try_refund")
def test_fulfillment_refund_products_fulfillment_lines_and_order_lines(
    mocked_refund,
    warehouse,
    variant,
    channel_USD,
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
        is_shipping_required=variant.is_shipping_required(),
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
        order=fulfilled_order,
        user=staff_api_client.user,
        app=None,
        payment=payment_dummy,
        manager=ANY,
        channel_slug=fulfilled_order.channel.slug,
        amount=amount,
    )


@pytest.mark.parametrize(
    "number_of_shipping_costs, should_raise_error", [(0, False), (1, False), (2, True)]
)
def test_fulfillment_refund_products_checks_shipping_costs_in_payments(
    number_of_shipping_costs,
    should_raise_error,
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
            "paymentsToRefund": [
                {
                    "paymentId": graphene.Node.to_global_id("Payment", payment_1.id),
                    "amount": payment_1.captured_amount,
                    "includeShippingCosts": True
                    if number_of_shipping_costs > 0
                    else False,
                },
                {
                    "paymentId": graphene.Node.to_global_id("Payment", payment_2.id),
                    "amount": payment_2.captured_amount,
                    "includeShippingCosts": True
                    if number_of_shipping_costs > 1
                    else False,
                },
            ],
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]

    # then
    if should_raise_error:
        assert data["fulfillment"] is None
        assert data["errors"][0]["field"] == "includeShippingCosts"
        assert data["errors"][0]["code"] == OrderErrorCode.DUPLICATED_INPUT_ITEM.name
        message = "Shipping costs cannot be included in more than one payment."
        assert data["errors"][0]["message"] == message

    else:
        assert data["errors"] == []
        assert data["fulfillment"] is not None


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
                    "includeShippingCosts": False,
                },
                {
                    "paymentId": graphene.Node.to_global_id("Payment", payment_2.id),
                    "amount": payment_2.captured_amount,
                    "includeShippingCosts": False,
                },
            ],
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


@pytest.mark.parametrize(
    "number_of_payments, should_raise_error", [(1, False), (2, True)]
)
def test_fulfillment_refund_products_with_amount_to_refund_requires_only_one_payment(
    number_of_payments,
    should_raise_error,
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

    payments = [payment_1]
    if number_of_payments == 2:
        payments.append(payment_2)

    fulfilled_order.payments.set(payments)

    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    variables = {"order": order_id, "input": {"amountToRefund": "11.00"}}

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_REFUND_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentRefundProducts"]

    # then
    if should_raise_error:
        assert data["fulfillment"] is None
        assert data["errors"][0]["field"] == "amountToRefund"
        assert (
            data["errors"][0]["code"] == OrderErrorCode.ORDER_HAS_MULTIPLE_PAYMENTS.name
        )
        message = (
            "It is not possible to use the amount field "
            "for orders with multiple payments."
        )
        assert data["errors"][0]["message"] == message
    else:
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
            "paymentsToRefund": [
                {
                    "paymentId": graphene.Node.to_global_id("Payment", payment_1.id),
                    "amount": payment_1.captured_amount,
                    "includeShippingCosts": False,
                },
                {
                    "paymentId": graphene.Node.to_global_id("Payment", payment_2.id),
                    "includeShippingCosts": True,
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
