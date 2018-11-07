from decimal import Decimal
from unittest.mock import patch

import pytest

from razorpay.errors import BadRequestError, ServerError
from saleor.payment import ChargeStatus, TransactionKind
from saleor.payment.gateways.razorpay import (
    ERROR_MSG_INVALID_REQUEST, ERROR_MSG_ORDER_NOT_CHARGED,
    ERROR_MSG_SERVER_ERROR, ERROR_UNSUPPORTED_CURRENCY, charge,
    clean_razorpay_response, get_amount_for_razorpay, get_client,
    get_client_token, get_form_class, logger, refund)
from saleor.payment.gateways.razorpay.forms import (
    RazorPayCheckoutWidget, RazorPaymentForm)

TRANSACTION_AMOUNT = Decimal('61.33')


@pytest.fixture()
def gateway_params():
    return {
        'public_key': 'public',
        'secret_key': 'secret',
        'prefill': True,
        'store_name': 'Saleor',
        'store_image': 'image.png'}


@pytest.fixture()
def razorpay_success_response():
    return {
        'id': 'transaction123',
        'amount': get_amount_for_razorpay(TRANSACTION_AMOUNT),
        'currency': 'INR'}


@pytest.fixture()
def razorpay_payment(payment_dummy):
    payment_dummy.currency = 'INR'
    return payment_dummy


@pytest.fixture()
def charged_payment(razorpay_payment):
    razorpay_payment.captured_amount = razorpay_payment.total
    razorpay_payment.charge_status = ChargeStatus.CHARGED
    razorpay_payment.save(update_fields=['captured_amount', 'charge_status'])

    razorpay_payment.transactions.create(
        amount=razorpay_payment.total,
        kind=TransactionKind.CHARGE,
        gateway_response={},
        is_success=True)
    return razorpay_payment


def test_checkout_widget_render_without_prefill(razorpay_payment, gateway_params):
    gateway_params['prefill'] = False
    widget = RazorPayCheckoutWidget(
        payment=razorpay_payment, attrs={'data-custom': '123'},
        **gateway_params)
    assert widget.render() == (
        '<script data-amount="8000" data-buttontext="Pay now with Razorpay" '
        'data-currency="INR" data-custom="123" '
        'data-description="Total payment" '
        'data-image="image.png" data-key="public" data-name="Saleor" '
        'src="https://checkout.razorpay.com/v1/checkout.js"></script>')


def test_checkout_widget_render_with_prefill(razorpay_payment, gateway_params):
    widget = RazorPayCheckoutWidget(
        payment=razorpay_payment, **gateway_params)
    assert widget.render() == (
        '<script data-amount="8000" data-buttontext="Pay now with Razorpay" '
        'data-currency="INR" data-description="Total payment" '
        'data-image="image.png" data-key="public" data-name="Saleor" '
        'data-prefill.email="test@example.com" '
        'data-prefill.name="Doe John" '
        'src="https://checkout.razorpay.com/v1/checkout.js"></script>')


def test_checkout_form(razorpay_payment, gateway_params):
    form = RazorPaymentForm(
        data={'razorpay_payment_id': '123'},
        payment=razorpay_payment,
        gateway=None, gateway_params=gateway_params)
    assert form.is_valid()
    with patch.object(razorpay_payment, 'charge') as mocked_charge:
        assert form.process_payment() == razorpay_payment
        mocked_charge.assert_called_once_with('123')


def test_get_amount_for_razorpay():
    assert get_amount_for_razorpay(Decimal('61.33')) == 6133


def test_clean_razorpay_response():
    response = {'amount': 6133}
    clean_razorpay_response(response)
    assert response['amount'] == Decimal('61.33')


@patch('razorpay.Client')
def test_get_client(mocked_gateway, gateway_params):
    get_client(**gateway_params)
    mocked_gateway.assert_called_once_with(auth=('public', 'secret'))


def test_get_client_token():
    assert get_client_token()


def test_get_form_class():
    assert get_form_class() == RazorPaymentForm


@pytest.mark.integration
@patch('razorpay.Client')
def test_charge(
        mocked_gateway,
        razorpay_payment,
        razorpay_success_response,
        gateway_params):

    # Data to be passed
    payment_token = '123'

    # Mock the gateway response to a success response
    mocked_gateway.return_value.payment.capture.return_value = (
        razorpay_success_response)

    # Attempt charging
    txn, error = charge(
        razorpay_payment, payment_token,
        TRANSACTION_AMOUNT, **gateway_params)

    # Ensure the was no error returned
    assert not error
    assert txn.is_success

    assert txn.payment == razorpay_payment
    assert txn.kind == TransactionKind.CHARGE
    assert txn.amount == TRANSACTION_AMOUNT
    assert txn.currency == razorpay_success_response['currency']
    assert txn.gateway_response == {}
    assert txn.token == razorpay_success_response['id']


@pytest.mark.integration
def test_charge_unsupported_currency(razorpay_payment, gateway_params):
    # Set the payment currency to an unsupported currency
    razorpay_payment.currency = 'USD'

    # Data to be passed
    payment_token = '123'

    # Attempt charging
    txn, error = charge(
        razorpay_payment, payment_token,
        TRANSACTION_AMOUNT, **gateway_params)

    # Ensure a error was returned
    assert error == ERROR_UNSUPPORTED_CURRENCY % {'currency': 'USD'}
    assert not txn.is_success

    # Ensure the transaction is correctly set
    assert txn.payment == razorpay_payment
    assert txn.kind == TransactionKind.CHARGE
    assert txn.token == payment_token


@patch.object(logger, 'exception')
@patch('razorpay.Client')
def test_charge_invalid_request(
        mocked_gateway,
        mocked_logger,
        razorpay_payment,
        gateway_params):

    # Data to be passed
    payment_token = '123'

    # Assign the side effect to the gateway's `charge()` method,
    # that should trigger the expected error.
    mocked_gateway.return_value.payment.capture.side_effect = BadRequestError()

    # Attempt charging
    txn, error = charge(
        razorpay_payment, payment_token,
        TRANSACTION_AMOUNT, **gateway_params)

    # Ensure an error was returned
    assert error == ERROR_MSG_INVALID_REQUEST
    assert not txn.is_success

    # Ensure the transaction is correctly set
    assert txn.payment == razorpay_payment
    assert txn.kind == TransactionKind.CHARGE
    assert txn.token == payment_token

    # Ensure the HTTP error was logged
    assert mocked_logger.call_count == 1


@pytest.mark.integration
@patch('razorpay.Client')
def test_refund(
        mocked_gateway,
        charged_payment,
        razorpay_success_response,
        gateway_params):

    # Mock the gateway response to a success response
    mocked_gateway.return_value.payment.refund.return_value = (
        razorpay_success_response)

    # Attempt charging
    txn, error = refund(
        charged_payment, TRANSACTION_AMOUNT, **gateway_params)

    # Ensure the was no error returned
    assert not error
    assert txn.is_success

    assert txn.payment == charged_payment
    assert txn.kind == TransactionKind.REFUND
    assert txn.amount == TRANSACTION_AMOUNT
    assert txn.currency == razorpay_success_response['currency']
    assert txn.gateway_response == {}
    assert txn.token == razorpay_success_response['id']


@pytest.mark.integration
def test_refund_unsupported_currency(
        razorpay_payment, charged_payment, gateway_params):
    # Set the payment currency to an unsupported currency
    razorpay_payment.currency = 'USD'

    # Attempt charging
    txn, error = refund(
        razorpay_payment, TRANSACTION_AMOUNT, **gateway_params)

    # Ensure a error was returned
    assert error == ERROR_UNSUPPORTED_CURRENCY % {'currency': 'USD'}
    assert not txn.is_success

    # Ensure the transaction is correctly set
    assert txn.payment == razorpay_payment
    assert txn.kind == TransactionKind.REFUND


@pytest.mark.integration
@patch('razorpay.Client')
def test_refund_not_paid(
        mocked_gateway,
        razorpay_payment,
        razorpay_success_response,
        gateway_params):

    # Mock the gateway response to a success response
    mocked_gateway.return_value.payment.refund.return_value = (
        razorpay_success_response)

    # Attempt charging
    txn, error = refund(
        razorpay_payment, TRANSACTION_AMOUNT, **gateway_params)

    # Ensure a error was returned
    assert error == ERROR_MSG_ORDER_NOT_CHARGED
    assert not txn.is_success

    # Ensure the transaction is correctly set
    assert txn.payment == razorpay_payment
    assert txn.kind == TransactionKind.REFUND


@pytest.mark.integration
@patch.object(logger, 'exception')
@patch('razorpay.Client')
def test_refund_invalid_data(
        mocked_gateway,
        mocked_logger,
        charged_payment,
        razorpay_success_response,
        gateway_params):

    # Assign the side effect to the gateway's `refund()` method,
    # that should trigger the expected error.
    mocked_gateway.return_value.payment.refund.side_effect = ServerError()

    # Attempt charging
    txn, error = refund(
        charged_payment, TRANSACTION_AMOUNT, **gateway_params)

    # Ensure a error was returned
    assert error == ERROR_MSG_SERVER_ERROR
    assert not txn.is_success

    # Ensure the transaction is correctly set
    assert txn.payment == charged_payment
    assert txn.kind == TransactionKind.REFUND

    # Ensure the HTTP error was logged
    assert mocked_logger.call_count == 1
