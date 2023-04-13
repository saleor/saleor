import graphene
from mock import patch

from .....payment import TransactionKind
from .....payment.models import ChargeStatus
from .....tests.utils import flush_post_commit_hooks
from ....core.enums import PaymentErrorCode
from ....tests.utils import get_graphql_content

REFUND_QUERY = """
    mutation PaymentRefund($paymentId: ID!, $amount: PositiveDecimal) {
        paymentRefund(paymentId: $paymentId, amount: $amount) {
            payment {
                id,
                chargeStatus
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
def test_payment_refund_success(
    mock_order_fully_refunded,
    mock_order_refunded,
    mock_order_updated,
    staff_api_client,
    permission_manage_orders,
    payment_txn_captured,
    order_with_lines,
):
    # given
    payment = payment_txn_captured
    payment.total = order_with_lines.total.gross.amount
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": str(payment.total)}

    # when
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentRefund"]
    assert not data["errors"]
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_REFUNDED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.REFUND

    flush_post_commit_hooks()
    mock_order_updated.assert_called_once_with(payment.order)
    mock_order_refunded.assert_called_once_with(payment.order)
    mock_order_fully_refunded.assert_called_once_with(payment.order)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
def test_payment_refund_with_invalid_argument(
    mock_order_fully_refunded,
    mock_order_refunded,
    mock_order_updated,
    staff_api_client,
    permission_manage_orders,
    payment_txn_captured,
):
    # given
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": 0}

    # when
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentRefund"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "Amount should be a positive number."

    assert not mock_order_fully_refunded.called
    assert not mock_order_refunded.called
    assert not mock_order_updated.called


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
def test_payment_refund_error(
    mock_order_fully_refunded,
    mock_order_refunded,
    mock_order_updated,
    staff_api_client,
    permission_manage_orders,
    payment_txn_captured,
    monkeypatch,
):
    # given
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id, "amount": str(payment.total)}
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)

    # when
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentRefund"]

    assert data["errors"] == [
        {
            "field": None,
            "message": "Unable to process refund",
            "code": PaymentErrorCode.PAYMENT_ERROR.name,
        }
    ]
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.REFUND
    assert not txn.is_success

    assert not mock_order_fully_refunded.called
    assert not mock_order_refunded.called
    assert not mock_order_updated.called
