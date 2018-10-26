from decimal import Decimal

import pytest

from saleor.payment import ChargeStatus, PaymentError, TransactionType


def test_authorize(payment_dummy):
    txn = payment_dummy.authorize(transaction_token='Fake')
    assert txn.is_success
    assert txn.transaction_type == TransactionType.AUTH
    assert txn.payment == payment_dummy
    payment_dummy.refresh_from_db()
    assert payment_dummy.is_active


def test_authorize_gateway_error(payment_dummy, monkeypatch):
    monkeypatch.setattr(
        'saleor.payment.gateways.dummy.dummy_success', lambda: False)
    with pytest.raises(PaymentError):
        txn = payment_dummy.authorize(transaction_token='Fake')
        assert txn.transaction_type == TransactionType.AUTH
        assert not txn.is_success
        assert txn.payment == payment_dummy


def test_void_success(payment_dummy):
    assert payment_dummy.is_active
    assert payment_dummy.charge_status == ChargeStatus.NOT_CHARGED
    txn = payment_dummy.void()
    assert txn.is_success
    assert txn.transaction_type == TransactionType.VOID
    assert txn.payment == payment_dummy
    payment_dummy.refresh_from_db()
    assert not payment_dummy.is_active
    assert payment_dummy.charge_status == ChargeStatus.NOT_CHARGED


@pytest.mark.parametrize(
    'is_active, charge_status', [
        (False, ChargeStatus.NOT_CHARGED),
        (False, ChargeStatus.CHARGED),
        (True, ChargeStatus.CHARGED),
        (True, ChargeStatus.FULLY_REFUNDED), ])
def test_void_failed(is_active, charge_status, payment_dummy):
    payment = payment_dummy
    payment.is_active = is_active
    payment.charge_status = charge_status
    payment.save()
    with pytest.raises(PaymentError):
        txn = payment.void()
        assert txn is None


def test_void_gateway_error(payment_dummy, monkeypatch):
    monkeypatch.setattr(
        'saleor.payment.gateways.dummy.dummy_success', lambda: False)
    with pytest.raises(PaymentError):
        txn = payment_dummy.void()
        assert txn.transaction_type == TransactionType.VOID
        assert not txn.is_success
        assert txn.payment == payment_dummy


@pytest.mark.parametrize('amount', [80, 70])
def test_charge_success(amount, payment_dummy):
    txn = payment_dummy.capture(amount=amount)
    assert txn.is_success
    assert txn.payment == payment_dummy
    payment_dummy.refresh_from_db()
    assert payment_dummy.charge_status == ChargeStatus.CHARGED
    assert payment_dummy.is_active


@pytest.mark.parametrize(
    'amount, captured_amount, charge_status, is_active', [
        (80, 0, ChargeStatus.NOT_CHARGED, False),
        (80, 0, ChargeStatus.FULLY_REFUNDED, True),
        (80, 80, ChargeStatus.CHARGED, True),
        (120, 0, ChargeStatus.NOT_CHARGED, True), ])
def test_charge_failed(
        amount, captured_amount, charge_status, is_active,
        payment_dummy):
    payment = payment_dummy
    payment.is_active = is_active
    payment.captured_amount = captured_amount
    payment.charge_status = charge_status
    payment.save()
    with pytest.raises(PaymentError):
        txn = payment.capture(amount=amount)
        assert txn is None


def test_charge_gateway_error(payment_dummy, monkeypatch):
    monkeypatch.setattr(
        'saleor.payment.gateways.dummy.dummy_success', lambda: False)
    with pytest.raises(PaymentError):
        txn = payment_dummy.capture(80)
        assert txn.transaction_type == TransactionType.CHARGE
        assert not txn.is_success
        assert txn.payment == payment_dummy


@pytest.mark.parametrize(
    'initial_captured_amount, refund_amount, final_captured_amount, final_charge_status, active_after',
    [
        (80, 80, 0, ChargeStatus.FULLY_REFUNDED, False),
        (80, 10, 70, ChargeStatus.CHARGED, True), ])
def test_refund_success(
        initial_captured_amount, refund_amount, final_captured_amount,
        final_charge_status, active_after, payment_dummy):
    payment = payment_dummy
    payment.charge_status = ChargeStatus.CHARGED
    payment.captured_amount = initial_captured_amount
    payment.save()
    txn = payment.refund(refund_amount)
    assert txn.transaction_type == TransactionType.REFUND
    assert txn.is_success
    assert txn.payment == payment
    assert payment.charge_status == final_charge_status
    assert payment.captured_amount == final_captured_amount
    assert payment.is_active == active_after


@pytest.mark.parametrize(
    'initial_captured_amount, refund_amount, initial_charge_status', [
        (80, 0, ChargeStatus.FULLY_REFUNDED),
        (0, 10, ChargeStatus.NOT_CHARGED),
        (10, 20, ChargeStatus.CHARGED), ])
def test_refund_failed(
        initial_captured_amount, refund_amount, initial_charge_status,
        payment_dummy):
    payment = payment_dummy
    payment.charge_status = initial_charge_status
    payment.captured_amount = Decimal(initial_captured_amount)
    payment.save()
    with pytest.raises(PaymentError):
        txn = payment.refund(refund_amount)
        assert txn is None


def test_refund_gateway_error(payment_dummy, monkeypatch):
    monkeypatch.setattr(
        'saleor.payment.gateways.dummy.dummy_success', lambda: False)
    payment = payment_dummy
    payment.charge_status = ChargeStatus.CHARGED
    payment.captured_amount = Decimal('80.00')
    payment.save()
    with pytest.raises(PaymentError):
        payment.refund(Decimal('80.00'))

    payment.refresh_from_db()
    txn = payment.transactions.first()
    assert txn.transaction_type == TransactionType.REFUND
    assert not txn.is_success
    assert txn.payment == payment
    assert payment.charge_status == ChargeStatus.CHARGED
    assert payment.captured_amount == Decimal('80.00')
