from decimal import Decimal
from unittest.mock import patch

from ...plugins.manager import get_plugins_manager
from .. import ChargeStatus, CustomPaymentChoices, TransactionKind, gateway
from ..interface import GatewayResponse
from ..utils import create_payment_information

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


@patch("saleor.payment.gateway.update_payment")
def test_process_payment(
    update_payment_mock, fake_payment_interface, payment_txn_preauth
):
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_preauth, payment_token=TOKEN
    )
    fake_payment_interface.process_payment.return_value = PROCESS_PAYMENT_RESPONSE

    transaction = gateway.process_payment(
        payment=payment_txn_preauth,
        token=TOKEN,
        manager=fake_payment_interface,
        channel_slug=payment_txn_preauth.order.channel.slug,
    )

    fake_payment_interface.process_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA, channel_slug=payment_txn_preauth.order.channel.slug
    )
    assert transaction.amount == PROCESS_PAYMENT_RESPONSE.amount
    assert transaction.kind == TransactionKind.CAPTURE
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE
    update_payment_mock.assert_called_once_with(
        payment_txn_preauth, PROCESS_PAYMENT_RESPONSE
    )


def test_store_source_when_processing_payment(
    fake_payment_interface, payment_txn_preauth
):
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_preauth, payment_token=TOKEN, store_source=True
    )
    fake_payment_interface.process_payment.return_value = PROCESS_PAYMENT_RESPONSE

    transaction = gateway.process_payment(
        payment=payment_txn_preauth,
        token=TOKEN,
        manager=fake_payment_interface,
        store_source=True,
        channel_slug=payment_txn_preauth.order.channel.slug,
    )

    fake_payment_interface.process_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA, channel_slug=payment_txn_preauth.order.channel.slug
    )
    assert transaction.customer_id == PROCESS_PAYMENT_RESPONSE.customer_id


@patch("saleor.payment.gateway.update_payment")
def test_authorize_payment(update_payment_mock, fake_payment_interface, payment_dummy):
    PAYMENT_DATA = create_payment_information(
        payment=payment_dummy, payment_token=TOKEN
    )
    fake_payment_interface.authorize_payment.return_value = AUTHORIZE_RESPONSE

    transaction = gateway.authorize(
        payment=payment_dummy,
        token=TOKEN,
        manager=fake_payment_interface,
        channel_slug=payment_dummy.order.channel.slug,
    )

    fake_payment_interface.authorize_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA, channel_slug=payment_dummy.order.channel.slug
    )
    assert transaction.amount == AUTHORIZE_RESPONSE.amount
    assert transaction.kind == TransactionKind.AUTH
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE
    update_payment_mock.assert_called_once_with(payment_dummy, AUTHORIZE_RESPONSE)


@patch("saleor.payment.gateway.update_payment")
def test_capture_payment(
    update_payment_mock, fake_payment_interface, payment_txn_preauth
):
    auth_transaction = payment_txn_preauth.transactions.get()
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_preauth, payment_token=auth_transaction.token
    )
    fake_payment_interface.capture_payment.return_value = PROCESS_PAYMENT_RESPONSE

    transaction = gateway.capture(
        payment=payment_txn_preauth,
        manager=fake_payment_interface,
        channel_slug=payment_txn_preauth.order.channel.slug,
    )

    fake_payment_interface.capture_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA, channel_slug=payment_txn_preauth.order.channel.slug
    )
    assert transaction.amount == PROCESS_PAYMENT_RESPONSE.amount
    assert transaction.kind == TransactionKind.CAPTURE
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE
    update_payment_mock.assert_called_once_with(
        payment_txn_preauth, PROCESS_PAYMENT_RESPONSE
    )


def test_refund_for_manual_payment(payment_txn_captured):
    payment_txn_captured.gateway = CustomPaymentChoices.MANUAL
    transaction = gateway.refund(
        payment=payment_txn_captured,
        manager=get_plugins_manager(),
        amount=PARTIAL_REFUND_AMOUNT,
        channel_slug=payment_txn_captured.order.channel.slug,
    )
    payment_txn_captured.refresh_from_db()
    assert payment_txn_captured.charge_status == ChargeStatus.PARTIALLY_REFUNDED
    assert transaction.amount == PARTIAL_REFUND_AMOUNT
    assert transaction.kind == TransactionKind.REFUND
    assert transaction.currency == "USD"


def test_partial_refund_payment(fake_payment_interface, payment_txn_captured):
    capture_transaction = payment_txn_captured.transactions.get()
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_captured,
        amount=PARTIAL_REFUND_AMOUNT,
        payment_token=capture_transaction.token,
    )
    fake_payment_interface.refund_payment.return_value = PARTIAL_REFUND_RESPONSE
    transaction = gateway.refund(
        payment=payment_txn_captured,
        manager=fake_payment_interface,
        amount=PARTIAL_REFUND_AMOUNT,
        channel_slug=payment_txn_captured.order.channel.slug,
    )
    fake_payment_interface.refund_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA, channel_slug=payment_txn_captured.order.channel.slug
    )

    payment_txn_captured.refresh_from_db()
    assert payment_txn_captured.charge_status == ChargeStatus.PARTIALLY_REFUNDED
    assert transaction.amount == PARTIAL_REFUND_AMOUNT
    assert transaction.kind == TransactionKind.REFUND
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE


def test_full_refund_payment(fake_payment_interface, payment_txn_captured):
    capture_transaction = payment_txn_captured.transactions.get()
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_captured,
        amount=FULL_REFUND_AMOUNT,
        payment_token=capture_transaction.token,
    )
    fake_payment_interface.refund_payment.return_value = FULL_REFUND_RESPONSE
    transaction = gateway.refund(
        payment=payment_txn_captured,
        manager=fake_payment_interface,
        channel_slug=payment_txn_captured.order.channel.slug,
    )
    fake_payment_interface.refund_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA, channel_slug=payment_txn_captured.order.channel.slug
    )

    payment_txn_captured.refresh_from_db()
    assert payment_txn_captured.charge_status == ChargeStatus.FULLY_REFUNDED
    assert transaction.amount == FULL_REFUND_AMOUNT
    assert transaction.kind == TransactionKind.REFUND
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE


def test_void_payment(fake_payment_interface, payment_txn_preauth):
    auth_transaction = payment_txn_preauth.transactions.get()
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_preauth,
        payment_token=auth_transaction.token,
        amount=VOID_AMOUNT,
    )
    fake_payment_interface.void_payment.return_value = VOID_RESPONSE

    transaction = gateway.void(
        payment=payment_txn_preauth,
        manager=fake_payment_interface,
        channel_slug=payment_txn_preauth.order.channel.slug,
    )

    fake_payment_interface.void_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA, channel_slug=payment_txn_preauth.order.channel.slug
    )
    payment_txn_preauth.refresh_from_db()
    assert not payment_txn_preauth.is_active
    assert transaction.amount == VOID_RESPONSE.amount
    assert transaction.kind == TransactionKind.VOID
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE


@patch("saleor.payment.gateway.update_payment")
def test_confirm_payment(
    update_payment_mock, fake_payment_interface, payment_txn_to_confirm
):
    auth_transaction = payment_txn_to_confirm.transactions.get()
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_to_confirm,
        payment_token=auth_transaction.token,
        amount=CONFIRM_AMOUNT,
    )
    fake_payment_interface.confirm_payment.return_value = CONFIRM_RESPONSE

    transaction = gateway.confirm(
        payment=payment_txn_to_confirm,
        manager=fake_payment_interface,
        channel_slug=payment_txn_to_confirm.order.channel.slug,
    )

    fake_payment_interface.confirm_payment.assert_called_once_with(
        USED_GATEWAY,
        PAYMENT_DATA,
        channel_slug=payment_txn_to_confirm.order.channel.slug,
    )
    assert transaction.amount == CONFIRM_RESPONSE.amount
    assert transaction.kind == TransactionKind.CONFIRM
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE
    update_payment_mock.assert_called_once_with(
        payment_txn_to_confirm, CONFIRM_RESPONSE
    )


def test_list_gateways(fake_payment_interface):
    gateways = [{"name": "Stripe"}, {"name": "Braintree"}]
    fake_payment_interface.list_payment_gateways.return_value = gateways
    lst = gateway.list_gateways(fake_payment_interface)
    fake_payment_interface.list_payment_gateways.assert_called_once()
    assert lst == gateways
