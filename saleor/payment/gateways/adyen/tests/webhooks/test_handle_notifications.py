from decimal import Decimal
from unittest import mock

import graphene
import pytest

from ......order import OrderStatus
from ..... import ChargeStatus, TransactionKind
from ...utils import to_adyen_price
from ...webhooks import (
    create_new_transaction,
    handle_authorization,
    handle_cancel_or_refund,
    handle_cancellation,
    handle_capture,
    handle_failed_capture,
    handle_failed_refund,
    handle_pending,
    handle_refund,
    handle_reversed_refund,
    webhook_not_implemented,
)


def test_handle_authorization(notification, adyen_plugin, payment_adyen_for_order):
    payment = payment_adyen_for_order
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    handle_authorization(notification, config)

    assert payment.transactions.count() == 1
    transaction = payment.transactions.get()
    assert transaction.is_success is True
    assert transaction.kind == TransactionKind.AUTH


def test_handle_authorization_with_adyen_auto_capture(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    config.connection_params["adyen_auto_capture"] = True
    handle_authorization(notification, config)

    assert payment.transactions.count() == 1
    assert payment.transactions.get().kind == TransactionKind.CAPTURE


@pytest.mark.vcr
def test_handle_authorization_with_auto_capture(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        psp_reference="853596537720508F",
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    config.auto_capture = True
    config.connection_params["adyen_auto_capture"] = False

    handle_authorization(notification, config)

    payment.refresh_from_db()
    assert payment.transactions.count() == 2
    assert payment.transactions.first().kind == TransactionKind.AUTH
    assert payment.transactions.last().kind == TransactionKind.CAPTURE
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED


def test_handle_authorization_with_adyen_auto_capture_and_payment_charged(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    config.connection_params["adyen_auto_capture"] = True
    handle_authorization(notification, config)

    # payment already has a charge status no need to handle auth action
    assert payment.transactions.count() == 0


def test_handle_cancel(notification, adyen_plugin, payment_adyen_for_order):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    handle_cancellation(notification, config)

    payment.order.refresh_from_db()
    assert payment.transactions.count() == 1
    transaction = payment.transactions.get()
    assert transaction.is_success is True
    assert transaction.kind == TransactionKind.CANCEL

    assert payment.order.status == OrderStatus.CANCELED


def test_handle_cancel_already_canceleld(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    create_new_transaction(notification, payment, TransactionKind.CANCEL)

    handle_cancellation(notification, config)

    assert payment.transactions.count() == 1


@mock.patch("saleor.payment.gateways.adyen.webhooks.order_captured")
def test_handle_capture(
    mocked_captured, notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    handle_capture(notification, config)

    assert payment.transactions.count() == 1
    transaction = payment.transactions.get()
    assert transaction.is_success is True
    assert transaction.kind == TransactionKind.CAPTURE
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    mocked_captured.assert_called_once_with(
        payment.order, None, transaction.amount, payment
    )


def test_handle_capture_with_payment_already_charged(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    handle_capture(notification, config)

    # Payment is already captured so no need to save capture transaction
    assert payment.transactions.count() == 0


@pytest.mark.parametrize(
    "charge_status", [ChargeStatus.NOT_CHARGED, ChargeStatus.FULLY_CHARGED]
)
def test_handle_failed_capture(
    charge_status, notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = charge_status
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    handle_failed_capture(notification, config)

    assert payment.transactions.count() == 1
    transaction = payment.transactions.get()
    assert transaction.is_success is True
    assert transaction.kind == TransactionKind.CAPTURE_FAILED
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.NOT_CHARGED


def test_handle_failed_capture_partial_charge(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount += payment.total * 2
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    handle_failed_capture(notification, config)

    assert payment.transactions.count() == 1
    transaction = payment.transactions.get()
    assert transaction.is_success is True
    assert transaction.kind == TransactionKind.CAPTURE_FAILED
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.PARTIALLY_CHARGED


def test_handle_pending(notification, adyen_plugin, payment_adyen_for_order):
    payment = payment_adyen_for_order
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    handle_pending(notification, config)

    assert payment.transactions.count() == 1
    transaction = payment.transactions.get()
    assert transaction.is_success is True
    assert transaction.kind == TransactionKind.PENDING
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.PENDING


def test_handle_pending_with_adyen_auto_capture(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    config.connection_params["adyen_auto_capture"] = True

    handle_pending(notification, config)

    # in case of autocapture we don't want to store the pending status as all payments
    # by default get capture status.
    assert payment.transactions.count() == 1
    assert payment.transactions.get().kind == TransactionKind.PENDING
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.PENDING


def test_handle_pending_already_pending(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.PENDING
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    create_new_transaction(notification, payment, TransactionKind.PENDING)

    handle_pending(notification, config)

    assert payment.transactions.count() == 1


@mock.patch("saleor.payment.gateways.adyen.webhooks.order_refunded")
def test_handle_refund(
    mock_order_refunded, notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    handle_refund(notification, config)

    assert payment.transactions.count() == 1
    transaction = payment.transactions.get()
    assert transaction.is_success is True
    assert transaction.kind == TransactionKind.REFUND
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_REFUNDED
    assert payment.captured_amount == Decimal("0.00")

    mock_order_refunded.assert_called_once_with(
        payment.order, None, transaction.amount, payment
    )


@mock.patch("saleor.payment.gateways.adyen.webhooks.order_refunded")
def test_handle_refund_already_refunded(
    mock_order_refunded, notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_REFUNDED
    payment.captured_amount = Decimal("0.00")
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    create_new_transaction(notification, payment, TransactionKind.REFUND)
    config = adyen_plugin().config

    handle_refund(notification, config)

    assert payment.transactions.count() == 1
    assert not mock_order_refunded.called


def test_handle_failed_refund_missing_transaction(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    handle_failed_refund(notification, config)

    assert payment.transactions.count() == 0


def test_handle_failed_refund_with_transaction_refund_ongoing(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    create_new_transaction(notification, payment, TransactionKind.REFUND_ONGOING)
    handle_failed_refund(notification, config)

    assert (
        payment.transactions.count() == 3
    )  # REFUND_ONGOING, REFUND_FAILED, FULLY_CHARGED
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.total == payment.captured_amount


def test_handle_failed_refund_with_transaction_refund(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_REFUNDED
    payment.captured_amount = Decimal("0.0")
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    create_new_transaction(notification, payment, TransactionKind.REFUND)
    handle_failed_refund(notification, config)

    payment.refresh_from_db()
    assert payment.transactions.count() == 3  # REFUND, REFUND_FAILED, FULLY_CHARGED
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.total == payment.captured_amount


def test_handle_reversed_refund(notification, adyen_plugin, payment_adyen_for_order):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_REFUNDED
    payment.captured_amount = Decimal("0.0")
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    handle_reversed_refund(notification, config)

    payment.refresh_from_db()
    assert payment.transactions.count() == 1  # REFUND_REVERSED
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.total == payment.captured_amount


def test_handle_reversed_refund_already_processed(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    create_new_transaction(notification, payment, TransactionKind.REFUND_REVERSED)
    handle_reversed_refund(notification, config)

    payment.refresh_from_db()
    assert payment.transactions.count() == 1


def test_webhook_not_implemented(notification, adyen_plugin, payment_adyen_for_order):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    webhook_not_implemented(notification, config)

    assert payment.order.events.count() == 1


@mock.patch("saleor.payment.gateways.adyen.webhooks.handle_refund")
def test_handle_cancel_or_refund_action_refund(
    mock_handle_refund, notification, adyen_plugin, payment_adyen_for_order
):

    payment = payment_adyen_for_order
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    config = adyen_plugin().config
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    notification["additionalData"]["modification.action"] = "refund"

    handle_cancel_or_refund(notification, config)

    mock_handle_refund.assert_called_once_with(notification, config)


@mock.patch("saleor.payment.gateways.adyen.webhooks.handle_cancellation")
def test_handle_cancel_or_refund_action_cancel(
    mock_handle_cancellation, notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    config = adyen_plugin().config
    notification = notification(
        merchant_reference=payment_id,
        value=to_adyen_price(payment.total, payment.currency),
    )
    notification["additionalData"]["modification.action"] = "cancel"

    handle_cancel_or_refund(notification, config)

    mock_handle_cancellation.assert_called_once_with(notification, config)
