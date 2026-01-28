from decimal import Decimal

import pytest

from .....plugins.manager import get_plugins_manager
from .... import ChargeStatus, PaymentError, TransactionKind, gateway


@pytest.fixture(autouse=True)
def setup_cod_gateway(settings):
    settings.PLUGINS = [
        "saleor.payment.gateways.cash_on_delivery.plugin.CashOnDeliveryGatewayPlugin"
    ]
    return settings


def test_authorize_success(payment_dummy):
    txn = gateway.authorize(
        payment=payment_dummy,
        token="COD",
        manager=get_plugins_manager(allow_replica=False),
        channel_slug=payment_dummy.order.channel.slug,
    )
    assert txn.is_success
    assert txn.kind == TransactionKind.AUTH
    assert txn.payment == payment_dummy
    payment_dummy.refresh_from_db()
    assert payment_dummy.is_active


def test_void_success(payment_txn_preauth):
    assert payment_txn_preauth.is_active
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    txn = gateway.void(
        payment=payment_txn_preauth,
        manager=get_plugins_manager(allow_replica=False),
        channel_slug=payment_txn_preauth.order.channel.slug,
    )
    assert txn.is_success
    assert txn.kind == TransactionKind.VOID
    assert txn.payment == payment_txn_preauth
    payment_txn_preauth.refresh_from_db()
    assert not payment_txn_preauth.is_active
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED


@pytest.mark.parametrize(
    ("amount", "charge_status"),
    [("98.40", ChargeStatus.FULLY_CHARGED), (70, ChargeStatus.PARTIALLY_CHARGED)],
)
def test_capture_success(amount, charge_status, payment_txn_preauth):
    txn = gateway.capture(
        payment=payment_txn_preauth,
        manager=get_plugins_manager(allow_replica=False),
        amount=Decimal(amount),
        channel_slug=payment_txn_preauth.order.channel.slug,
    )
    assert txn.is_success
    assert txn.payment == payment_txn_preauth
    payment_txn_preauth.refresh_from_db()
    assert payment_txn_preauth.charge_status == charge_status
    assert payment_txn_preauth.is_active


@pytest.mark.parametrize(
    (
        "initial_captured_amount",
        "refund_amount",
        "final_captured_amount",
        "final_charge_status",
        "active_after",
    ),
    [
        (80, 80, 0, ChargeStatus.FULLY_REFUNDED, False),
        (80, 10, 70, ChargeStatus.PARTIALLY_REFUNDED, True),
    ],
)
def test_refund_success(
    initial_captured_amount,
    refund_amount,
    final_captured_amount,
    final_charge_status,
    active_after,
    payment_txn_captured,
):
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = initial_captured_amount
    payment.save()
    txn = gateway.refund(
        payment=payment,
        manager=get_plugins_manager(allow_replica=False),
        amount=Decimal(refund_amount),
        channel_slug=payment.order.channel.slug,
    )

    payment.refresh_from_db()
    assert txn.kind == TransactionKind.REFUND
    assert txn.is_success
    assert txn.payment == payment
    assert payment.charge_status == final_charge_status
    assert payment.captured_amount == final_captured_amount
    assert payment.is_active == active_after
