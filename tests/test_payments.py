import pytest

from saleor.payment import (
    PaymentError, PaymentMethodChargeStatus, TransactionType)


def test_authorize(payment_method_dummy):
    txn = payment_method_dummy.authorize()
    assert txn.is_success
    assert txn.transaction_type == TransactionType.AUTH
    assert txn.payment_method == payment_method_dummy
    payment_method_dummy.refresh_from_db()
    assert payment_method_dummy.is_active


def test_authorize_gateway_error(payment_method_dummy, monkeypatch):
    monkeypatch.setattr(
        'saleor.payment.providers.dummy.dummy_success', lambda: False)
    with pytest.raises(PaymentError):
        txn = payment_method_dummy.authorize()
        assert txn.transaction_type == TransactionType.AUTH
        assert not txn.is_success
        assert txn.payment_method == payment_method_dummy


def test_void_success(payment_method_dummy):
    assert payment_method_dummy.is_active
    assert payment_method_dummy.charge_status == PaymentMethodChargeStatus.NOT_CHARGED
    txn = payment_method_dummy.void()
    assert txn.is_success
    assert txn.transaction_type == TransactionType.VOID
    assert txn.payment_method == payment_method_dummy
    payment_method_dummy.refresh_from_db()
    assert not payment_method_dummy.is_active
    assert payment_method_dummy.charge_status == PaymentMethodChargeStatus.NOT_CHARGED


@pytest.mark.parametrize(
    'is_active, charge_status', [
        (False, PaymentMethodChargeStatus.NOT_CHARGED),
        (False, PaymentMethodChargeStatus.CHARGED),
        (True, PaymentMethodChargeStatus.CHARGED),
        (True, PaymentMethodChargeStatus.FULLY_REFUNDED), ])
def test_void_failed(is_active, charge_status, payment_method_dummy):
    payment_method = payment_method_dummy
    payment_method.is_active = is_active
    payment_method.charge_status = charge_status
    payment_method.save()
    with pytest.raises(PaymentError):
        txn = payment_method.void()
        assert txn is None


def test_void_gateway_error(payment_method_dummy, monkeypatch):
    monkeypatch.setattr(
        'saleor.payment.providers.dummy.dummy_success', lambda: False)
    with pytest.raises(PaymentError):
        txn = payment_method_dummy.authorize()
        assert txn.transaction_type == TransactionType.VOID
        assert not txn.is_success
        assert txn.payment_method == payment_method_dummy


@pytest.mark.parametrize('amount', [100, 90])
def test_charge_success(amount, payment_method_dummy):
    txn = payment_method_dummy.charge(amount=amount)
    assert txn.is_success
    assert txn.payment_method == payment_method_dummy
    payment_method_dummy.refresh_from_db()
    assert payment_method_dummy.charge_status == PaymentMethodChargeStatus.CHARGED
    assert payment_method_dummy.is_active


@pytest.mark.parametrize(
    'amount, captured_amount, charge_status, is_active', [
        (100, 0, PaymentMethodChargeStatus.NOT_CHARGED, False),
        (100, 0, PaymentMethodChargeStatus.FULLY_REFUNDED, True),
        (100, 100, PaymentMethodChargeStatus.CHARGED, True),
        (120, 0, PaymentMethodChargeStatus.NOT_CHARGED, True), ])
def test_charge_failed(
        amount, captured_amount, charge_status, is_active,
        payment_method_dummy):
    payment_method = payment_method_dummy
    payment_method.is_active = is_active
    payment_method.captured_amount = captured_amount
    payment_method.charge_status = charge_status
    payment_method.save()
    with pytest.raises(PaymentError):
        txn = payment_method.charge(amount=amount)
        assert txn is None


def test_charge_gateway_error(payment_method_dummy, monkeypatch):
    monkeypatch.setattr(
        'saleor.payment.providers.dummy.dummy_success', lambda: False)
    with pytest.raises(PaymentError):
        txn = payment_method_dummy.charge(100)
        assert txn.transaction_type == TransactionType.CHARGE
        assert not txn.is_success
        assert txn.payment_method == payment_method_dummy


@pytest.mark.parametrize(
    'initial_captured_amount, refund_amount, final_captured_amount, final_charge_status, active_after',
    [
        (100, 100, 0, PaymentMethodChargeStatus.FULLY_REFUNDED, False),
        (100, 10, 90, PaymentMethodChargeStatus.CHARGED, True), ])
def test_refund_success(
        initial_captured_amount, refund_amount, final_captured_amount,
        final_charge_status, active_after, payment_method_dummy):
    payment_method = payment_method_dummy
    payment_method.charge_status = PaymentMethodChargeStatus.CHARGED
    payment_method.captured_amount = initial_captured_amount
    payment_method.save()
    txn = payment_method.refund(refund_amount)
    assert txn.transaction_type == TransactionType.REFUND
    assert txn.is_success
    assert txn.payment_method == payment_method
    assert payment_method.charge_status == final_charge_status
    assert payment_method.captured_amount == final_captured_amount
    assert payment_method.is_active == active_after


@pytest.mark.parametrize(
    'initial_captured_amount, refund_amount, initial_charge_status', [
        (100, 0, PaymentMethodChargeStatus.FULLY_REFUNDED),
        (0, 10, PaymentMethodChargeStatus.NOT_CHARGED),
        (10, 20, PaymentMethodChargeStatus.CHARGED), ])
def test_refund_failed(
        initial_captured_amount, refund_amount, initial_charge_status,
        payment_method_dummy):
    payment_method = payment_method_dummy
    payment_method.charge_status = initial_charge_status
    payment_method.captured_amount = initial_captured_amount
    payment_method.save()
    with pytest.raises(PaymentError):
        txn = payment_method.refund(refund_amount)
        assert txn is None


def test_refund_gateway_error(payment_method_dummy, monkeypatch):
    monkeypatch.setattr(
        'saleor.payment.providers.dummy.dummy_success', lambda: False)
    payment_method = payment_method_dummy
    payment_method.charge_status = PaymentMethodChargeStatus.CHARGED
    payment_method.captured_amount = 100
    payment_method.save()
    with pytest.raises(PaymentError):
        txn = payment_method.refund(100)
        payment_method.refresh_from_db()
        assert txn.transaction_type == TransactionType.REFUND
        assert not txn.is_success
        assert txn.payment_method == payment_method
        assert payment_method.charge_status == PaymentMethodChargeStatus.CHARGED
        assert payment_method.captured_amount == 100
