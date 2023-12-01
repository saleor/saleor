from decimal import Decimal
from unittest import mock
from unittest.mock import ANY, patch

import graphene
from prices import Money, TaxedMoney

from .....core.prices import quantize_price
from .....order import FulfillmentLineData, OrderOrigin, OrderStatus
from .....order.error_codes import OrderErrorCode
from .....order.fetch import OrderLineInfo
from .....order.models import FulfillmentStatus, Order
from .....payment import ChargeStatus, PaymentError
from .....payment.interface import RefundData
from .....tests.utils import flush_post_commit_hooks
from .....warehouse.models import Stock
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content

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


def test_fulfillment_return_products_by_user_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    fulfilled_order,
    channel_PLN,
    payment_dummy,
):
    # given
    fulfilled_order.channel = channel_PLN
    fulfilled_order.save(update_fields=["channel"])

    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)

    order_id = to_global_id_or_none(fulfilled_order)
    amount_to_refund = Decimal("11.00")
    variables = {
        "order": order_id,
        "input": {
            "refund": True,
            "amountToRefund": amount_to_refund,
            "includeShippingCosts": True,
        },
    }
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    # then
    assert_no_permission(response)


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_return_products_by_app(
    mocked_refund,
    app_api_client,
    permission_manage_orders,
    fulfilled_order,
    payment_dummy,
):
    # given
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    fulfilled_order.payments.add(payment_dummy)

    order_id = to_global_id_or_none(fulfilled_order)
    amount_to_refund = Decimal("11.00")
    variables = {
        "order": order_id,
        "input": {
            "refund": True,
            "amountToRefund": amount_to_refund,
            "includeShippingCosts": True,
        },
    }

    # when
    response = app_api_client.post_graphql(
        ORDER_FULFILL_RETURN_MUTATION,
        variables,
        permissions=(permission_manage_orders,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
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


def test_fulfillment_return_products_order_without_payment(
    staff_api_client, permission_group_manage_orders, fulfilled_order
):
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.pk)
    variables = {
        "order": order_id,
        "input": {"refund": True, "amountToRefund": "11.00"},
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
        "input": {
            "refund": True,
            "amountToRefund": amount_to_refund,
            "includeShippingCosts": True,
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

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


def test_fulfillment_return_products_amount_order_with_gift_card(
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
        "input": {
            "refund": True,
            "amountToRefund": amount_to_refund,
            "includeShippingCosts": True,
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    fulfillment = data["returnFulfillment"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "amountToRefund"
    assert errors[0]["code"] == OrderErrorCode.CANNOT_REFUND.name
    assert fulfillment is None


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_return_products_refund_raising_payment_error(
    mocked_refund,
    staff_api_client,
    permission_group_manage_orders,
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.CANNOT_REFUND.name


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_return_products_order_lines(
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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


def test_fulfillment_return_products_gift_card_order_line(
    staff_api_client,
    permission_group_manage_orders,
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    fulfillment = data["returnFulfillment"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "orderLineId"
    assert errors[0]["code"] == OrderErrorCode.GIFT_CARD_LINE.name
    assert fulfillment is None


def test_fulfillment_return_products_order_lines_quantity_bigger_than_total(
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
        "input": {
            "orderLines": [{"orderLineId": line_id, "quantity": 200, "replace": False}]
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    staff_api_client, permission_group_manage_orders, order_with_lines, payment_dummy
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
        amount=amount_to_refund,
        channel_slug=order_with_lines.channel.slug,
        refund_data=RefundData(
            order_lines_to_refund=[
                OrderLineInfo(
                    line=line_to_return,
                    quantity=2,
                    variant=line_to_return.variant,
                )
            ],
            refund_amount_is_automatically_calculated=False,
        ),
    )


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_return_products_fulfillment_lines(
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
        amount=amount,
        channel_slug=fulfilled_order.channel.slug,
        refund_data=RefundData(
            fulfillment_lines_to_refund=[
                FulfillmentLineData(
                    line=fulfillment_line_to_return,
                    quantity=quantity_to_return,
                ),
            ],
            refund_shipping_costs=True,
        ),
    )


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_return_products_gift_card_fulfillment_line(
    mocked_refund,
    staff_api_client,
    permission_group_manage_orders,
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    fulfillment = data["returnFulfillment"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "fulfillmentLineId"
    assert errors[0]["code"] == OrderErrorCode.GIFT_CARD_LINE.name
    assert fulfillment is None


def test_fulfillment_return_products_fulfillment_lines_quantity_bigger_than_total(
    staff_api_client, permission_group_manage_orders, fulfilled_order, payment_dummy
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    staff_api_client, permission_group_manage_orders, fulfilled_order, payment_dummy
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    staff_api_client, permission_group_manage_orders, fulfilled_order, payment_dummy
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    permission_group_manage_orders,
    fulfilled_order,
    payment_dummy,
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
        amount=amount,
        channel_slug=fulfilled_order.channel.slug,
        refund_data=RefundData(
            fulfillment_lines_to_refund=[
                FulfillmentLineData(line=fulfillment_line_to_return, quantity=2)
            ],
            refund_shipping_costs=True,
        ),
    )


@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_return_products_fulfillment_lines_and_order_lines(
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)

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
        amount=amount,
        channel_slug=fulfilled_order.channel.slug,
        refund_data=RefundData(
            order_lines_to_refund=[
                OrderLineInfo(
                    line=order_line,
                    quantity=2,
                    variant=variant,
                )
            ],
        ),
    )


@patch("saleor.order.actions.order_refunded")
@patch("saleor.order.actions.gateway.refund")
def test_fulfillment_return_products_calls_order_refunded(
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
    # given
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    # then
    flush_post_commit_hooks()
    amount = order_line.unit_price_gross_amount * 2
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
