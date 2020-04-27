from decimal import Decimal

import pytest

import saleor.payment.gateway as gateway
from saleor.payment import ChargeStatus, TransactionKind
from saleor.payment.interface import GatewayResponse
from saleor.payment.utils import create_payment_information

RAW_RESPONSE = {"test": "abcdefgheijklmn"}
PROCESS_PAYMENT_RESPONSE = GatewayResponse(
    is_success=True,
    customer_id="test_customer",
    action_required=False,
    kind=TransactionKind.CAPTURE,
    amount=Decimal(10.0),
    currency="usd",
    transaction_id="1234",
    error=None,
    raw_response=RAW_RESPONSE,
)
AUTHORIZE_RESPONSE = GatewayResponse(
    is_success=True,
    customer_id="test_customer",
    action_required=False,
    kind=TransactionKind.AUTH,
    amount=Decimal(10.0),
    currency="usd",
    transaction_id="1234",
    error=None,
    raw_response=RAW_RESPONSE,
)
VOID_AMOUNT = Decimal("98.40")
VOID_RESPONSE = GatewayResponse(
    is_success=True,
    customer_id="test_customer",
    action_required=False,
    kind=TransactionKind.VOID,
    amount=VOID_AMOUNT,
    currency="usd",
    transaction_id="1234",
    error=None,
    raw_response=RAW_RESPONSE,
)
PARTIAL_REFUND_AMOUNT = Decimal(2.0)
PARTIAL_REFUND_RESPONSE = GatewayResponse(
    is_success=True,
    customer_id="test_customer",
    action_required=False,
    kind=TransactionKind.REFUND,
    amount=PARTIAL_REFUND_AMOUNT,
    currency="usd",
    transaction_id="1234",
    error=None,
    raw_response=RAW_RESPONSE,
)
FULL_REFUND_AMOUNT = Decimal("98.40")
FULL_REFUND_RESPONSE = GatewayResponse(
    is_success=True,
    customer_id="test_customer",
    action_required=False,
    kind=TransactionKind.REFUND,
    amount=FULL_REFUND_AMOUNT,
    currency="usd",
    transaction_id="1234",
    error=None,
    raw_response=RAW_RESPONSE,
)
CONFIRM_AMOUNT = Decimal("98.40")
CONFIRM_RESPONSE = GatewayResponse(
    is_success=True,
    customer_id="test_customer",
    action_required=False,
    kind=TransactionKind.CONFIRM,
    amount=CONFIRM_AMOUNT,
    currency="usd",
    transaction_id="1234",
    error=None,
    raw_response=RAW_RESPONSE,
)
TOKEN = "token"
USED_GATEWAY = "mirumee.payments.dummy"


@pytest.fixture
def mock_payment_interface(mocker, fake_payment_interface):
    mgr = mocker.patch(
        "saleor.payment.gateway.get_plugins_manager",
        autospec=True,
        return_value=fake_payment_interface,
    )
    yield fake_payment_interface
    mgr.assert_called_once()


def test_process_payment(mock_payment_interface, payment_txn_preauth):
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_preauth, payment_token=TOKEN
    )
    mock_payment_interface.process_payment.return_value = PROCESS_PAYMENT_RESPONSE

    transaction = gateway.process_payment(payment=payment_txn_preauth, token=TOKEN)

    mock_payment_interface.process_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA
    )
    assert transaction.amount == PROCESS_PAYMENT_RESPONSE.amount
    assert transaction.kind == TransactionKind.CAPTURE
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE


def test_store_source_when_processing_payment(
    mock_payment_interface, payment_txn_preauth
):
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_preauth, payment_token=TOKEN, store_source=True
    )
    mock_payment_interface.process_payment.return_value = PROCESS_PAYMENT_RESPONSE

    transaction = gateway.process_payment(
        payment=payment_txn_preauth, token=TOKEN, store_source=True
    )

    mock_payment_interface.process_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA
    )
    assert transaction.customer_id == PROCESS_PAYMENT_RESPONSE.customer_id


def test_authorize_payment(mock_payment_interface, payment_dummy):
    PAYMENT_DATA = create_payment_information(
        payment=payment_dummy, payment_token=TOKEN
    )
    mock_payment_interface.authorize_payment.return_value = AUTHORIZE_RESPONSE

    transaction = gateway.authorize(payment=payment_dummy, token=TOKEN)

    mock_payment_interface.authorize_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA
    )
    assert transaction.amount == AUTHORIZE_RESPONSE.amount
    assert transaction.kind == TransactionKind.AUTH
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE


def test_capture_payment(mock_payment_interface, payment_txn_preauth):
    auth_transaction = payment_txn_preauth.transactions.get()
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_preauth, payment_token=auth_transaction.token
    )
    mock_payment_interface.capture_payment.return_value = PROCESS_PAYMENT_RESPONSE

    transaction = gateway.capture(payment=payment_txn_preauth)

    mock_payment_interface.capture_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA
    )
    assert transaction.amount == PROCESS_PAYMENT_RESPONSE.amount
    assert transaction.kind == TransactionKind.CAPTURE
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE


def test_partial_refund_payment(mock_payment_interface, payment_txn_captured):
    capture_transaction = payment_txn_captured.transactions.get()
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_captured,
        amount=PARTIAL_REFUND_AMOUNT,
        payment_token=capture_transaction.token,
    )
    mock_payment_interface.refund_payment.return_value = PARTIAL_REFUND_RESPONSE
    transaction = gateway.refund(
        payment=payment_txn_captured, amount=PARTIAL_REFUND_AMOUNT
    )
    mock_payment_interface.refund_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA
    )

    payment_txn_captured.refresh_from_db()
    assert payment_txn_captured.charge_status == ChargeStatus.PARTIALLY_REFUNDED
    assert transaction.amount == PARTIAL_REFUND_AMOUNT
    assert transaction.kind == TransactionKind.REFUND
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE


def test_full_refund_payment(mock_payment_interface, payment_txn_captured):
    capture_transaction = payment_txn_captured.transactions.get()
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_captured,
        amount=FULL_REFUND_AMOUNT,
        payment_token=capture_transaction.token,
    )
    mock_payment_interface.refund_payment.return_value = FULL_REFUND_RESPONSE
    transaction = gateway.refund(payment=payment_txn_captured)
    mock_payment_interface.refund_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA
    )

    payment_txn_captured.refresh_from_db()
    assert payment_txn_captured.charge_status == ChargeStatus.FULLY_REFUNDED
    assert transaction.amount == FULL_REFUND_AMOUNT
    assert transaction.kind == TransactionKind.REFUND
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE


def test_void_payment(mock_payment_interface, payment_txn_preauth):
    auth_transaction = payment_txn_preauth.transactions.get()
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_preauth,
        payment_token=auth_transaction.token,
        amount=VOID_AMOUNT,
    )
    mock_payment_interface.void_payment.return_value = VOID_RESPONSE

    transaction = gateway.void(payment=payment_txn_preauth)

    mock_payment_interface.void_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA
    )
    payment_txn_preauth.refresh_from_db()
    assert not payment_txn_preauth.is_active
    assert transaction.amount == VOID_RESPONSE.amount
    assert transaction.kind == TransactionKind.VOID
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE


def test_confirm_payment(mock_payment_interface, payment_txn_to_confirm):
    auth_transaction = payment_txn_to_confirm.transactions.get()
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_to_confirm,
        payment_token=auth_transaction.token,
        amount=CONFIRM_AMOUNT,
    )
    mock_payment_interface.confirm_payment.return_value = CONFIRM_RESPONSE

    transaction = gateway.confirm(payment=payment_txn_to_confirm)

    mock_payment_interface.confirm_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA
    )
    assert transaction.amount == CONFIRM_RESPONSE.amount
    assert transaction.kind == TransactionKind.CONFIRM
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE


def test_list_gateways(mock_payment_interface):
    gateways = [{"name": "Stripe"}, {"name": "Braintree"}]
    mock_payment_interface.list_payment_gateways.return_value = gateways
    lst = gateway.list_gateways()
    mock_payment_interface.list_payment_gateways.assert_called_once()
    assert lst == gateways
