from unittest.mock import patch

import graphene

from .....payment import TransactionKind
from .....payment.models import ChargeStatus
from .....tests.utils import flush_post_commit_hooks
from ....core.enums import PaymentErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content

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
    permission_group_manage_orders,
    payment_txn_captured,
    order_with_lines,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    payment = payment_txn_captured
    payment.total = order_with_lines.total.gross.amount
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": str(payment.total)}

    # when
    response = staff_api_client.post_graphql(REFUND_QUERY, variables)

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


def test_payment_refund_success_by_user_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    payment_txn_captured,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    payment = payment_txn_captured

    order = payment.order
    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": str(payment.total)}

    # when
    response = staff_api_client.post_graphql(REFUND_QUERY, variables)

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
def test_payment_refund_success_by_app(
    mock_order_fully_refunded,
    mock_order_refunded,
    mock_order_updated,
    app_api_client,
    permission_manage_orders,
    payment_txn_captured,
):
    # given
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": str(payment.total)}

    # when
    response = app_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=(permission_manage_orders,)
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
    permission_group_manage_orders,
    payment_txn_captured,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": 0}

    # when
    response = staff_api_client.post_graphql(REFUND_QUERY, variables)

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
    permission_group_manage_orders,
    payment_txn_captured,
    monkeypatch,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id, "amount": str(payment.total)}
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)

    # when
    response = staff_api_client.post_graphql(REFUND_QUERY, variables)

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
