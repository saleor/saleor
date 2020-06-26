from decimal import Decimal

import pytest

from .... import ChargeStatus, PaymentError, TransactionKind, gateway
from .. import PREAUTHORIZED_TOKENS, TOKEN_VALIDATION_MAPPING, process_payment


@pytest.fixture(autouse=True)
def setup_dummy_gateway(settings):
    settings.PLUGINS = ["saleor.payment.gateways.dummy.plugin.DummyGatewayPlugin"]
    return settings


def test_authorize_success(payment_dummy):
    txn = gateway.authorize(payment=payment_dummy, token="Fake")
    assert txn.is_success
    assert txn.kind == TransactionKind.AUTH
    assert txn.payment == payment_dummy
    payment_dummy.refresh_from_db()
    assert payment_dummy.is_active


@pytest.mark.parametrize(
    "is_active, charge_status",
    [
        (False, ChargeStatus.NOT_CHARGED),
        (False, ChargeStatus.PARTIALLY_CHARGED),
        (False, ChargeStatus.FULLY_CHARGED),
        (False, ChargeStatus.PARTIALLY_REFUNDED),
        (False, ChargeStatus.FULLY_REFUNDED),
        (True, ChargeStatus.PARTIALLY_CHARGED),
        (True, ChargeStatus.FULLY_CHARGED),
        (True, ChargeStatus.PARTIALLY_REFUNDED),
        (True, ChargeStatus.FULLY_REFUNDED),
    ],
)
def test_authorize_failed(is_active, charge_status, payment_dummy):
    payment = payment_dummy
    payment.is_active = is_active
    payment.charge_status = charge_status
    payment.save()
    with pytest.raises(PaymentError):
        txn = gateway.authorize(payment=payment, token="Fake")
        assert txn is None


def test_authorize_gateway_error(payment_dummy, monkeypatch):
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)
    with pytest.raises(PaymentError):
        txn = gateway.authorize(payment=payment_dummy, token="Fake")
        assert txn.kind == TransactionKind.AUTH
        assert not txn.is_success
        assert txn.payment == payment_dummy


def test_void_success(payment_txn_preauth):
    assert payment_txn_preauth.is_active
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    txn = gateway.void(payment=payment_txn_preauth)
    assert txn.is_success
    assert txn.kind == TransactionKind.VOID
    assert txn.payment == payment_txn_preauth
    payment_txn_preauth.refresh_from_db()
    assert not payment_txn_preauth.is_active
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED


@pytest.mark.parametrize(
    "is_active, charge_status",
    [
        (False, ChargeStatus.NOT_CHARGED),
        (False, ChargeStatus.PARTIALLY_CHARGED),
        (False, ChargeStatus.FULLY_CHARGED),
        (False, ChargeStatus.PARTIALLY_REFUNDED),
        (False, ChargeStatus.FULLY_REFUNDED),
        (True, ChargeStatus.PARTIALLY_CHARGED),
        (True, ChargeStatus.FULLY_CHARGED),
        (True, ChargeStatus.PARTIALLY_REFUNDED),
        (True, ChargeStatus.FULLY_REFUNDED),
    ],
)
def test_void_failed(is_active, charge_status, payment_dummy):
    payment = payment_dummy
    payment.is_active = is_active
    payment.charge_status = charge_status
    payment.save()
    with pytest.raises(PaymentError):
        txn = gateway.void(payment=payment)
        assert txn is None


def test_void_gateway_error(payment_txn_preauth, monkeypatch):
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)
    with pytest.raises(PaymentError):
        txn = gateway.void(payment=payment_txn_preauth)
        assert txn.kind == TransactionKind.VOID
        assert not txn.is_success
        assert txn.payment == payment_txn_preauth


@pytest.mark.parametrize(
    "amount, charge_status, token",
    [
        ("98.40", ChargeStatus.FULLY_CHARGED, "1111111111111111"),
        (70, ChargeStatus.PARTIALLY_CHARGED, "2222222222222222"),
        (70, ChargeStatus.PARTIALLY_CHARGED, "fake"),
    ],
)
def test_capture_success(amount, charge_status, token, payment_txn_preauth):
    transaction = payment_txn_preauth.transactions.last()
    transaction.token = token
    transaction.save()

    txn = gateway.capture(payment=payment_txn_preauth, amount=Decimal(amount))
    assert txn.is_success
    assert txn.payment == payment_txn_preauth
    assert not txn.error
    payment_txn_preauth.refresh_from_db()
    assert payment_txn_preauth.charge_status == charge_status
    assert payment_txn_preauth.is_active


@pytest.mark.parametrize(
    "amount, captured_amount, charge_status, is_active",
    [
        (80, 0, ChargeStatus.NOT_CHARGED, False),
        (120, 0, ChargeStatus.NOT_CHARGED, True),
        (80, 20, ChargeStatus.PARTIALLY_CHARGED, True),
        (80, 80, ChargeStatus.FULLY_CHARGED, True),
        (80, 0, ChargeStatus.FULLY_REFUNDED, True),
    ],
)
def test_capture_failed(
    amount, captured_amount, charge_status, is_active, payment_dummy
):
    payment = payment_dummy
    payment.is_active = is_active
    payment.captured_amount = captured_amount
    payment.charge_status = charge_status
    payment.save()
    with pytest.raises(PaymentError):
        txn = gateway.capture(payment=payment, amount=amount)
        assert txn is None


@pytest.mark.parametrize("token, error", list(TOKEN_VALIDATION_MAPPING.items()))
def test_capture_error_in_response(token, error, payment_txn_preauth):
    # given
    transaction = payment_txn_preauth.transactions.last()
    transaction.token = token
    transaction.save()

    # when
    with pytest.raises(PaymentError) as e:
        gateway.capture(payment=payment_txn_preauth)

    e._excinfo[1].message == error


@pytest.mark.parametrize(
    (
        "initial_captured_amount, refund_amount, final_captured_amount, "
        "final_charge_status, active_after"
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
    txn = gateway.refund(payment=payment, amount=Decimal(refund_amount))
    assert txn.kind == TransactionKind.REFUND
    assert txn.is_success
    assert txn.payment == payment
    assert payment.charge_status == final_charge_status
    assert payment.captured_amount == final_captured_amount
    assert payment.is_active == active_after


@pytest.mark.parametrize(
    "initial_captured_amount, refund_amount, initial_charge_status",
    [
        (0, 10, ChargeStatus.NOT_CHARGED),
        (10, 20, ChargeStatus.PARTIALLY_CHARGED),
        (10, 20, ChargeStatus.FULLY_CHARGED),
        (10, 20, ChargeStatus.PARTIALLY_REFUNDED),
        (80, 0, ChargeStatus.FULLY_REFUNDED),
    ],
)
def test_refund_failed(
    initial_captured_amount, refund_amount, initial_charge_status, payment_dummy
):
    payment = payment_dummy
    payment.charge_status = initial_charge_status
    payment.captured_amount = Decimal(initial_captured_amount)
    payment.save()
    with pytest.raises(PaymentError):
        txn = gateway.refund(payment=payment, amount=Decimal(refund_amount))
        assert txn is None


def test_refund_gateway_error(payment_txn_captured, monkeypatch):
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = Decimal("80.00")
    payment.save()
    with pytest.raises(PaymentError):
        gateway.refund(payment=payment, amount=Decimal("80.00"))

    payment.refresh_from_db()
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.REFUND
    assert not txn.is_success
    assert txn.payment == payment
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.captured_amount == Decimal("80.00")


@pytest.mark.parametrize("token", ["111", PREAUTHORIZED_TOKENS[1]])
def test_process_payment_success(token, payment_dummy):
    # when
    txn = gateway.process_payment(payment=payment_dummy, token=token)

    # then
    assert txn.is_success
    assert txn.payment == payment_dummy
    assert txn.kind == TransactionKind.CAPTURE
    assert not txn.error
    payment_dummy.refresh_from_db()
    assert payment_dummy.is_active


@pytest.mark.parametrize("token, error", list(TOKEN_VALIDATION_MAPPING.items()))
def test_process_payment_failed(token, error, payment_dummy):
    # when
    with pytest.raises(PaymentError) as e:
        gateway.process_payment(payment=payment_dummy, token=token)

    e._excinfo[1].message == error


@pytest.mark.parametrize("token", PREAUTHORIZED_TOKENS)
def test_process_payment_pre_authorized(
    token, payment_dummy, dummy_gateway_config, monkeypatch
):
    # given
    dummy_gateway_config.auto_capture = False
    monkeypatch.setattr(
        "saleor.payment.gateways.dummy.plugin.DummyGatewayPlugin._get_gateway_config",
        lambda _: dummy_gateway_config,
    )

    # when
    txn = gateway.process_payment(payment=payment_dummy, token=token)

    # then
    assert txn.is_success
    assert txn.payment == payment_dummy
    assert txn.kind == TransactionKind.AUTH
    assert not txn.error
    payment_dummy.refresh_from_db()
    assert payment_dummy.is_active


@pytest.mark.parametrize("token, error", list(TOKEN_VALIDATION_MAPPING.items()))
def test_process_payment_method_error_in_response(
    token, error, dummy_gateway_config, dummy_payment_data
):
    # given
    dummy_payment_data.token = token

    # when
    response = process_payment(dummy_payment_data, dummy_gateway_config)

    # then
    assert not response.is_success
    assert response.kind == TransactionKind.CAPTURE
    assert response.error == error
