from unittest.mock import patch

import pytest
from django.conf import settings

from saleor.payment import ChargeStatus, PaymentError, TransactionKind
from saleor.payment.gateways import razorpay
from saleor.payment.gateways.razorpay.forms import (
    RazorPayCheckoutWidget, RazorPaymentForm)


@pytest.fixture()
def mocked_gateway_client(razorpay_payment):
    with patch('razorpay.Client') as mocked:
        response = {'amount': int(razorpay_payment.total * 100)}
        mocked().payment.capture.return_value = response
        mocked().payment.refund.return_value = response
        yield mocked


@pytest.fixture()
def razorpay_payment(payment_dummy):
    payment_dummy.gateway = settings.RAZORPAY
    return payment_dummy


def _get_gateway_params(*, prefill=True):
    return {
        'prefill': prefill,
        'public_key': '123',
        'store_name': 'Saleor',
        'store_image': 'image.png'}


def test_checkout_widget_render_without_prefill(payment_dummy):
    widget = RazorPayCheckoutWidget(
        payment=payment_dummy, attrs={'data-custom': '123'},
        **_get_gateway_params(prefill=False))
    assert widget.render() == (
        '<script data-amount="8000" data-buttontext="Pay now with Razorpay" '
        'data-currency="USD" data-custom="123" '
        'data-description="Total payment" '
        'data-image="image.png" data-key="123" data-name="Saleor" '
        'src="https://checkout.razorpay.com/v1/checkout.js"></script>')


def test_checkout_widget_render_with_prefill(payment_dummy):
    widget = RazorPayCheckoutWidget(
        payment=payment_dummy, **_get_gateway_params(prefill=True))
    assert widget.render() == (
        '<script data-amount="8000" data-buttontext="Pay now with Razorpay" '
        'data-currency="USD" data-description="Total payment" '
        'data-image="image.png" data-key="123" data-name="Saleor" '
        'data-prefill.email="test@example.com" '
        'data-prefill.name="Doe John" '
        'src="https://checkout.razorpay.com/v1/checkout.js"></script>')


def test_checkout_form(payment_dummy):
    form = RazorPaymentForm(
        data={'razorpay_payment_id': '123'},
        payment=payment_dummy,
        gateway=None, gateway_params=_get_gateway_params())
    assert form.is_valid()
    with patch.object(payment_dummy, 'charge') as mocked_charge:
        assert form.process_payment() == payment_dummy
        mocked_charge.assert_called_once_with('123')


def test_gateway_get_form_class():
    assert razorpay.get_form_class() == RazorPaymentForm


def test_gateway_void(razorpay_payment):
    txn = razorpay_payment.void()
    razorpay_payment.refresh_from_db()

    assert txn.is_success
    assert txn.kind == TransactionKind.VOID
    assert txn.payment == razorpay_payment
    assert not razorpay_payment.is_active


def test_gateway_charge(mocked_gateway_client, razorpay_payment):
    capture_txn = razorpay_payment.charge(payment_token='token')

    mocked_gateway_client().payment.capture.assert_called_once_with(
        'token', int(razorpay_payment.total * 100))

    assert capture_txn.is_success
    assert capture_txn.kind == TransactionKind.CHARGE
    assert capture_txn.payment == razorpay_payment
    assert capture_txn.amount == razorpay_payment.total

    razorpay_payment.refresh_from_db()
    assert razorpay_payment.charge_status == ChargeStatus.CHARGED
    assert razorpay_payment.captured_amount == razorpay_payment.total
    assert razorpay_payment.is_active


def test_refund_success(mocked_gateway_client, razorpay_payment):
    razorpay_payment.captured_amount = razorpay_payment.total
    razorpay_payment.charge_status = ChargeStatus.CHARGED
    razorpay_payment.save(update_fields=['captured_amount', 'charge_status'])

    razorpay_payment.transactions.create(
        amount=razorpay_payment.total,
        kind=TransactionKind.CHARGE,
        gateway_response={},
        is_success=True)

    txn = razorpay_payment.refund()
    razorpay_payment.refresh_from_db()

    mocked_gateway_client().payment.refund.assert_called_once_with(
        razorpay_payment.token, int(razorpay_payment.total * 100))

    assert txn.payment == razorpay_payment
    assert txn.kind == TransactionKind.REFUND
    assert txn.amount == razorpay_payment.total
    assert txn.is_success

    assert razorpay_payment.charge_status == ChargeStatus.FULLY_REFUNDED
    assert not razorpay_payment.captured_amount
    assert not razorpay_payment.is_active


def test_refund_failed(mocked_gateway_client, razorpay_payment):
    razorpay_payment.captured_amount = razorpay_payment.total
    razorpay_payment.charge_status = ChargeStatus.CHARGED
    razorpay_payment.save(update_fields=['captured_amount', 'charge_status'])

    with pytest.raises(PaymentError, message=razorpay.E_ORDER_NOT_CHARGED):
        razorpay_payment.refund()

    razorpay_payment.refresh_from_db()
    txn = razorpay_payment.transactions.last()
    assert txn

    assert txn.payment == razorpay_payment
    assert txn.kind == TransactionKind.REFUND
    assert not txn.is_success

    assert mocked_gateway_client().payment.refund.call_count == 0

    assert razorpay_payment.charge_status == ChargeStatus.CHARGED
    assert razorpay_payment.captured_amount
    assert razorpay_payment.is_active
