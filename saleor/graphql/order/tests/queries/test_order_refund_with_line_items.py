from decimal import Decimal

from .....order import OrderGrantedRefundStatus
from .....order.utils import (
    calculate_order_granted_refund_status,
    update_order_charge_data,
)
from .....payment import TransactionEventType
from .....payment.models import TransactionEvent
from .....payment.transaction_item_calculations import recalculate_transaction_amounts
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

ORDER_PAYMENT_STATUS_QUERY = """
query OrderPaymentStatus($id: ID!) {
    order(id: $id) {
        totalCharged { amount }
        chargeStatus
        paymentStatus
        refundStatus
        grantedRefunds { status }
    }
}
"""


def _order_status(staff_api_client, permission_group_manage_orders, order):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(
        ORDER_PAYMENT_STATUS_QUERY, {"id": to_global_id_or_none(order)}
    )
    return get_graphql_content(response)["data"]["order"]


def test_refund_with_line_items_processed_by_app(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    """Refund with line items reported as successful by the payment app.

    This is the state the order ends up in after the Dashboard refunds an order per
    line item and the app processes the refund: the granted refund is successful and
    the transaction holds the refunded amount.
    """
    # given
    order = order_with_lines
    order_total = order.total_gross_amount
    transaction = transaction_item_generator(
        order_id=order.pk,
        charged_value=order_total,
        authorized_value=order_total,
    )
    granted_refund = order.granted_refunds.create(
        amount_value=order_total,
        currency=order.currency,
        transaction_item=transaction,
    )
    update_order_charge_data(order)

    granted_refund.refresh_from_db()
    assert granted_refund.status == OrderGrantedRefundStatus.NONE
    assert order.payment_transactions.get().refunded_value == Decimal(0)

    # when
    TransactionEvent.objects.create(
        transaction=transaction,
        psp_reference="refund-1",
        type=TransactionEventType.REFUND_SUCCESS,
        amount_value=order_total,
        include_in_calculations=True,
        currency=order.currency,
        related_granted_refund=granted_refund,
    )
    recalculate_transaction_amounts(transaction)
    calculate_order_granted_refund_status(granted_refund)
    update_order_charge_data(order)

    # then
    granted_refund.refresh_from_db()
    assert granted_refund.status == OrderGrantedRefundStatus.SUCCESS
    order_data = _order_status(staff_api_client, permission_group_manage_orders, order)
    assert order_data["paymentStatus"] == "FULLY_REFUNDED"
    assert order_data["refundStatus"] == "FULL"
    # a fully refunded order is not charged anymore, the Dashboard shows this status
    assert order_data["chargeStatus"] == "NONE"
    assert Decimal(order_data["totalCharged"]["amount"]) == Decimal(0)
    assert order_data["grantedRefunds"] == [{"status": "SUCCESS"}]
