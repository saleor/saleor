from decimal import Decimal

from .....core.prices import quantize_price
from .....order import OrderGrantedRefundStatus
from .....order.utils import update_order_charge_data
from .....payment import TransactionEventType
from .....payment.transaction_item_calculations import recalculate_transaction_amounts
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

ORDER_PAYMENT_STATUS_QUERY = """
query OrderPaymentStatus($id: ID!) {
    order(id: $id) {
        total { gross { amount currency } }
        totalCharged { amount currency }
        totalBalance { amount currency }
        chargeStatus
        paymentStatus
        refundStatus
    }
}
"""


def _get_order_data(staff_api_client, order, permission_group_manage_orders):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"id": to_global_id_or_none(order)}
    response = staff_api_client.post_graphql(ORDER_PAYMENT_STATUS_QUERY, variables)
    content = get_graphql_content(response)
    return content["data"]["order"]


def test_payment_status_pending_transaction_refund(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
    transaction_events_generator,
):
    """Refund with line items: the app has not processed the refund yet.

    The refunded money is not reported as successful yet, but it is already on its
    way back to the customer, so the order must not be reported as fully charged.
    """
    # given
    order = order_with_lines
    order_total = order.total_gross_amount
    transaction = transaction_item_generator(
        order_id=order.pk,
        charged_value=order_total,
        authorized_value=order_total,
    )
    transaction_events_generator(
        transaction=transaction,
        psp_references=["refund-1"],
        types=[TransactionEventType.REFUND_REQUEST],
        amounts=[order_total],
    )
    recalculate_transaction_amounts(transaction)
    update_order_charge_data(order)
    assert transaction.refund_pending_value == order_total

    # when
    order_data = _get_order_data(
        staff_api_client, order, permission_group_manage_orders
    )

    # then
    assert order_data["paymentStatus"] == "FULLY_REFUNDED"
    assert order_data["chargeStatus"] == "NONE"
    assert order_data["refundStatus"] == "FULL"
    # a pending refund must not turn the reported charged amount negative
    assert quantize_price(
        Decimal(order_data["totalCharged"]["amount"]), order.currency
    ) == quantize_price(Decimal(0), order.currency)
    # the balance compares what the customer paid with the order total, and the refund
    # in flight is already subtracted from the paid amount
    assert quantize_price(
        Decimal(order_data["totalBalance"]["amount"]), order.currency
    ) == quantize_price(-order_total, order.currency)


def test_payment_status_pending_partial_transaction_refund(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
    transaction_events_generator,
):
    # given
    order = order_with_lines
    order_total = order.total_gross_amount
    refund_amount = order_total / 2
    transaction = transaction_item_generator(
        order_id=order.pk,
        charged_value=order_total,
        authorized_value=order_total,
    )
    transaction_events_generator(
        transaction=transaction,
        psp_references=["refund-1"],
        types=[TransactionEventType.REFUND_REQUEST],
        amounts=[refund_amount],
    )
    recalculate_transaction_amounts(transaction)
    update_order_charge_data(order)

    # when
    order_data = _get_order_data(
        staff_api_client, order, permission_group_manage_orders
    )

    # then
    assert order_data["paymentStatus"] == "PARTIALLY_REFUNDED"
    assert order_data["refundStatus"] == "PARTIAL"
    # an unrefunded part of the order is still with the merchant, so the order is not
    # reported as fully charged
    assert order_data["chargeStatus"] == "NONE"


def test_payment_status_successful_transaction_refund(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
    transaction_events_generator,
):
    # given
    order = order_with_lines
    order_total = order.total_gross_amount
    transaction = transaction_item_generator(
        order_id=order.pk,
        charged_value=order_total,
        authorized_value=order_total,
    )
    transaction_events_generator(
        transaction=transaction,
        psp_references=["refund-1"],
        types=[TransactionEventType.REFUND_SUCCESS],
        amounts=[order_total],
    )
    recalculate_transaction_amounts(transaction)
    update_order_charge_data(order)

    # when
    order_data = _get_order_data(
        staff_api_client, order, permission_group_manage_orders
    )

    # then
    assert order_data["paymentStatus"] == "FULLY_REFUNDED"
    assert order_data["refundStatus"] == "FULL"
    assert quantize_price(
        Decimal(order_data["totalCharged"]["amount"]), order.currency
    ) == quantize_price(Decimal(0), order.currency)


def test_payment_status_charged_transaction_without_refund(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    order_total = order.total_gross_amount
    transaction_item_generator(
        order_id=order.pk,
        charged_value=order_total,
        authorized_value=order_total,
    )
    update_order_charge_data(order)

    # when
    order_data = _get_order_data(
        staff_api_client, order, permission_group_manage_orders
    )

    # then
    assert order_data["paymentStatus"] == "FULLY_CHARGED"
    assert order_data["refundStatus"] == "NONE"


def test_payment_status_granted_refund_is_not_a_refund_yet(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    """A refund that was only granted (not sent to the app) moves no money."""
    # given
    order = order_with_lines
    order_total = order.total_gross_amount
    transaction = transaction_item_generator(
        order_id=order.pk,
        charged_value=order_total,
        authorized_value=order_total,
    )
    order.granted_refunds.create(
        amount_value=order_total,
        currency=order.currency,
        transaction_item=transaction,
        status=OrderGrantedRefundStatus.PENDING,
    )
    update_order_charge_data(order)

    # when
    order_data = _get_order_data(
        staff_api_client, order, permission_group_manage_orders
    )

    # then
    assert order_data["paymentStatus"] == "FULLY_CHARGED"
    assert order_data["refundStatus"] == "NONE"


def test_payment_status_canceled_transaction(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    """A canceled charge is not money that the customer still owes.

    A successful cancellation leaves the charged amount on the transaction and reports
    the canceled amount next to it.
    """
    # given
    order = order_with_lines
    order_total = order.total_gross_amount
    transaction = transaction_item_generator(
        order_id=order.pk,
        charged_value=order_total,
        authorized_value=order_total,
    )
    transaction.canceled_value = order_total
    transaction.save(update_fields=["canceled_value"])
    update_order_charge_data(order)

    # when
    order_data = _get_order_data(
        staff_api_client, order, permission_group_manage_orders
    )

    # then
    assert order_data["paymentStatus"] == "NOT_CHARGED"
    assert order_data["chargeStatus"] == "NONE"
    # ``totalCharged`` reports what was charged, the canceled part is reported by the
    # transaction on its own
    assert quantize_price(
        Decimal(order_data["totalCharged"]["amount"]), order.currency
    ) == quantize_price(order_total, order.currency)
    # the charge covers the order total, so nothing is left to pay
    assert quantize_price(
        Decimal(order_data["totalBalance"]["amount"]), order.currency
    ) == quantize_price(Decimal(0), order.currency)


def test_payment_status_partially_canceled_transaction(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    """Only the canceled part of the charge is not charged anymore."""
    # given
    order = order_with_lines
    order_total = order.total_gross_amount
    canceled_amount = order_total / 2
    transaction = transaction_item_generator(
        order_id=order.pk,
        charged_value=order_total,
        authorized_value=order_total,
    )
    transaction.canceled_value = canceled_amount
    transaction.save(update_fields=["canceled_value"])
    update_order_charge_data(order)

    # when
    order_data = _get_order_data(
        staff_api_client, order, permission_group_manage_orders
    )

    # then
    assert order_data["paymentStatus"] == "PARTIALLY_CHARGED"
    assert order_data["chargeStatus"] == "PARTIAL"
    assert order_data["refundStatus"] == "NONE"
    assert quantize_price(
        Decimal(order_data["totalCharged"]["amount"]), order.currency
    ) == quantize_price(order_total, order.currency)
    # the cancellation moves no money here, the charge still covers the order total
    assert quantize_price(
        Decimal(order_data["totalBalance"]["amount"]), order.currency
    ) == quantize_price(Decimal(0), order.currency)
