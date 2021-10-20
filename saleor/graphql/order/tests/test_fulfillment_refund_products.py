from decimal import Decimal
from unittest.mock import ANY, patch

import graphene
from prices import Money, TaxedMoney

from ....core.prices import quantize_price
from ....order.error_codes import OrderErrorCode
from ....order.models import FulfillmentStatus
from ....payment import ChargeStatus, PaymentError
from ....warehouse.models import Stock
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
            orderLines
        }
    }
}
"""


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
        amount=quantize_price(amount_to_refund, fulfilled_order.currency),
        channel_slug=fulfilled_order.channel.slug,
    )


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
        payment_dummy,
        ANY,
        amount=fulfillment_line_to_refund.order_line.unit_price_gross_amount * 2,
        channel_slug=fulfilled_order.channel.slug,
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


@patch("saleor.order.actions.gateway.refund")
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
        payment_dummy, ANY, amount=amount, channel_slug=fulfilled_order.channel.slug
    )


@patch("saleor.order.actions.gateway.refund")
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
        payment_dummy, ANY, amount=amount, channel_slug=order_with_lines.channel.slug
    )


@patch("saleor.order.actions.gateway.refund")
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
        payment_dummy,
        ANY,
        amount=amount_to_refund,
        channel_slug=fulfilled_order.channel.slug,
    )


@patch("saleor.order.actions.gateway.refund")
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
        payment_dummy,
        ANY,
        amount=amount_to_refund,
        channel_slug=order_with_lines.channel.slug,
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
        payment_dummy, ANY, amount=amount, channel_slug=fulfilled_order.channel.slug
    )
