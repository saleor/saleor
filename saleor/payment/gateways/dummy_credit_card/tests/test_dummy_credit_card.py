from decimal import Decimal

import pytest

from .....plugins.manager import get_plugins_manager
from .... import ChargeStatus, PaymentError, TransactionKind, gateway
from .. import (
    PREAUTHORIZED_TOKENS,
    TOKEN_EXPIRED,
    TOKEN_VALIDATION_MAPPING,
    authorize,
    capture,
    process_payment,
    refund,
    void,
)
from ..plugin import DummyCreditCardGatewayPlugin

NO_LONGER_ACTIVE = "This payment is no longer active."
CANNOT_BE_AUTHORIZED_AGAIN = "Charged transactions cannot be authorized again."
LACK_OF_SUCCESSFUL_TRANSACTION = "Cannot find successful auth transaction."
CANNOT_BE_CAPTURED = "This payment cannot be captured."
CANNOT_REFUND_MORE_THAN_CAPTURE = "Cannot refund more than captured."
AMOUNT_SHOULD_BE_POSITIVE = "Amount should be a positive number."
CANNOT_CHARGE_MORE_THAN_UNCAPTURED = "Unable to charge more than un-captured amount."


@pytest.fixture(autouse=True)
def setup_dummy_credit_card_gateway(settings):
    DummyCreditCardGatewayPlugin.DEFAULT_ACTIVE = True
    settings.PLUGINS = [
        "saleor.payment.gateways.dummy_credit_card.plugin.DummyCreditCardGatewayPlugin"
    ]
    return settings


def test_authorize_success(payment_dummy_credit_card):
    txn = gateway.authorize(
        payment=payment_dummy_credit_card,
        token="Fake",
        manager=get_plugins_manager(allow_replica=False),
        channel_slug=payment_dummy_credit_card.order.channel.slug,
    )
    assert txn.is_success
    assert txn.kind == TransactionKind.AUTH
    assert txn.payment == payment_dummy_credit_card
    payment_dummy_credit_card.refresh_from_db()
    assert payment_dummy_credit_card.is_active


@pytest.mark.parametrize(
    ("is_active", "charge_status", "error"),
    [
        (False, ChargeStatus.NOT_CHARGED, NO_LONGER_ACTIVE),
        (False, ChargeStatus.PARTIALLY_CHARGED, NO_LONGER_ACTIVE),
        (False, ChargeStatus.FULLY_CHARGED, NO_LONGER_ACTIVE),
        (False, ChargeStatus.PARTIALLY_REFUNDED, NO_LONGER_ACTIVE),
        (False, ChargeStatus.FULLY_REFUNDED, NO_LONGER_ACTIVE),
        (True, ChargeStatus.PARTIALLY_CHARGED, CANNOT_BE_AUTHORIZED_AGAIN),
        (True, ChargeStatus.FULLY_CHARGED, CANNOT_BE_AUTHORIZED_AGAIN),
        (True, ChargeStatus.PARTIALLY_REFUNDED, CANNOT_BE_AUTHORIZED_AGAIN),
        (True, ChargeStatus.FULLY_REFUNDED, CANNOT_BE_AUTHORIZED_AGAIN),
    ],
)
def test_authorize_failed(is_active, charge_status, error, payment_dummy_credit_card):
    payment = payment_dummy_credit_card
    payment.is_active = is_active
    payment.charge_status = charge_status
    payment.save()
    with pytest.raises(PaymentError) as e:
        gateway.authorize(
            payment=payment,
            token="Fake",
            manager=get_plugins_manager(allow_replica=False),
            channel_slug=payment_dummy_credit_card.order.channel.slug,
        )

    assert e._excinfo[1].message == error


def test_authorize_gateway_error(payment_dummy_credit_card, monkeypatch):
    monkeypatch.setattr(
        "saleor.payment.gateways.dummy_credit_card.dummy_success", lambda: False
    )
    with pytest.raises(PaymentError) as e:
        gateway.authorize(
            payment=payment_dummy_credit_card,
            token="Fake",
            manager=get_plugins_manager(allow_replica=False),
            channel_slug=payment_dummy_credit_card.order.channel.slug,
        )

    assert e._excinfo[1].message == "Unable to authorize transaction"


def test_authorize_method_error(dummy_payment_data, dummy_gateway_config, monkeypatch):
    # given
    monkeypatch.setattr(
        "saleor.payment.gateways.dummy_credit_card.dummy_success", lambda: False
    )

    # when
    response = authorize(
        dummy_payment_data,
        dummy_gateway_config,
    )

    # then
    assert not response.is_success
    assert response.kind == TransactionKind.AUTH
    assert response.error == "Unable to authorize transaction"


def test_void_success(payment_txn_preauth):
    payment_txn_preauth.gateway = "mirumee.payments.dummy_credit_card"
    payment_txn_preauth.save()

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
    ("is_active", "charge_status", "error"),
    [
        (True, ChargeStatus.PARTIALLY_CHARGED, LACK_OF_SUCCESSFUL_TRANSACTION),
        (True, ChargeStatus.FULLY_CHARGED, LACK_OF_SUCCESSFUL_TRANSACTION),
        (True, ChargeStatus.PARTIALLY_REFUNDED, LACK_OF_SUCCESSFUL_TRANSACTION),
        (True, ChargeStatus.FULLY_REFUNDED, LACK_OF_SUCCESSFUL_TRANSACTION),
    ],
)
def test_void_failed(is_active, charge_status, error, payment_dummy_credit_card):
    payment = payment_dummy_credit_card
    payment.is_active = is_active
    payment.charge_status = charge_status
    payment.save()
    with pytest.raises(PaymentError) as e:
        gateway.void(
            payment=payment,
            manager=get_plugins_manager(allow_replica=False),
            channel_slug=payment.order.channel.slug,
        )

    assert e._excinfo[1].message == error


def test_void_gateway_error(payment_txn_preauth, monkeypatch):
    payment_txn_preauth.gateway = "mirumee.payments.dummy_credit_card"
    payment_txn_preauth.save()

    monkeypatch.setattr(
        "saleor.payment.gateways.dummy_credit_card.dummy_success", lambda: False
    )
    with pytest.raises(PaymentError) as e:
        gateway.void(
            payment=payment_txn_preauth,
            manager=get_plugins_manager(allow_replica=False),
            channel_slug=payment_txn_preauth.order.channel.slug,
        )

    assert e._excinfo[1].message == "Unable to void the transaction."


def test_void_method_error(dummy_payment_data, dummy_gateway_config, monkeypatch):
    # given
    monkeypatch.setattr(
        "saleor.payment.gateways.dummy_credit_card.dummy_success", lambda: False
    )

    # when
    response = void(dummy_payment_data, dummy_gateway_config)

    # then
    assert not response.is_success
    assert response.kind == TransactionKind.VOID
    assert response.error == "Unable to void the transaction."


@pytest.mark.parametrize(
    ("amount", "charge_status", "token"),
    [
        ("98.40", ChargeStatus.FULLY_CHARGED, "1111111111111111"),
        (70, ChargeStatus.PARTIALLY_CHARGED, "2222222222222222"),
        (70, ChargeStatus.PARTIALLY_CHARGED, "fake"),
    ],
)
def test_capture_success(amount, charge_status, token, payment_txn_preauth):
    payment_txn_preauth.gateway = "mirumee.payments.dummy_credit_card"
    payment_txn_preauth.save()
    transaction = payment_txn_preauth.transactions.last()
    transaction.token = token
    transaction.save()

    txn = gateway.capture(
        payment=payment_txn_preauth,
        manager=get_plugins_manager(allow_replica=False),
        amount=Decimal(amount),
        channel_slug=payment_txn_preauth.order.channel.slug,
    )
    assert txn.is_success
    assert txn.payment == payment_txn_preauth
    assert not txn.error
    payment_txn_preauth.refresh_from_db()
    assert payment_txn_preauth.charge_status == charge_status
    assert payment_txn_preauth.is_active


@pytest.mark.parametrize(
    ("amount", "captured_amount", "charge_status", "is_active", "error"),
    [
        (80, 0, ChargeStatus.NOT_CHARGED, False, NO_LONGER_ACTIVE),
        (120, 0, ChargeStatus.NOT_CHARGED, True, CANNOT_CHARGE_MORE_THAN_UNCAPTURED),
        (80, 20, ChargeStatus.PARTIALLY_CHARGED, True, CANNOT_BE_CAPTURED),
        (80, 80, ChargeStatus.FULLY_CHARGED, True, CANNOT_BE_CAPTURED),
        (80, 0, ChargeStatus.FULLY_REFUNDED, True, CANNOT_BE_CAPTURED),
    ],
)
def test_capture_failed(
    amount, captured_amount, charge_status, error, is_active, payment_dummy_credit_card
):
    payment = payment_dummy_credit_card
    payment.is_active = is_active
    payment.captured_amount = captured_amount
    payment.charge_status = charge_status
    payment.save()
    with pytest.raises(PaymentError) as e:
        gateway.capture(
            payment=payment,
            manager=get_plugins_manager(allow_replica=False),
            amount=amount,
            channel_slug=payment.order.channel.slug,
        )

    assert e._excinfo[1].message == error


@pytest.mark.parametrize(("token", "error"), list(TOKEN_VALIDATION_MAPPING.items()))
def test_capture_error_in_response(token, error, payment_txn_preauth):
    # given
    payment_txn_preauth.gateway = "mirumee.payments.dummy_credit_card"
    payment_txn_preauth.save()

    transaction = payment_txn_preauth.transactions.last()
    transaction.token = token
    transaction.save()

    # when
    with pytest.raises(PaymentError) as e:
        gateway.capture(
            payment=payment_txn_preauth,
            manager=get_plugins_manager(allow_replica=False),
            channel_slug=payment_txn_preauth.order.channel.slug,
        )

    assert e._excinfo[1].message == error


@pytest.mark.parametrize(("token", "error"), list(TOKEN_VALIDATION_MAPPING.items()))
def test_capture_method_error(
    token, error, dummy_payment_data, dummy_gateway_config, monkeypatch
):
    # given
    dummy_payment_data.token = token

    # when
    response = capture(dummy_payment_data, dummy_gateway_config)

    # then
    assert not response.is_success
    assert response.kind == TransactionKind.CAPTURE
    assert response.error == error


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
    payment.gateway = "mirumee.payments.dummy_credit_card"
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


@pytest.mark.parametrize(
    ("initial_captured_amount", "refund_amount", "initial_charge_status", "error"),
    [
        (0, 10, ChargeStatus.NOT_CHARGED, CANNOT_REFUND_MORE_THAN_CAPTURE),
        (10, 20, ChargeStatus.PARTIALLY_CHARGED, CANNOT_REFUND_MORE_THAN_CAPTURE),
        (10, 20, ChargeStatus.FULLY_CHARGED, CANNOT_REFUND_MORE_THAN_CAPTURE),
        (10, 20, ChargeStatus.PARTIALLY_REFUNDED, CANNOT_REFUND_MORE_THAN_CAPTURE),
        (80, 0, ChargeStatus.FULLY_REFUNDED, AMOUNT_SHOULD_BE_POSITIVE),
    ],
)
def test_refund_failed(
    initial_captured_amount,
    refund_amount,
    error,
    initial_charge_status,
    payment_dummy_credit_card,
):
    payment = payment_dummy_credit_card
    payment.charge_status = initial_charge_status
    payment.captured_amount = Decimal(initial_captured_amount)
    payment.save()
    with pytest.raises(PaymentError) as e:
        gateway.refund(
            payment=payment,
            manager=get_plugins_manager(allow_replica=False),
            amount=Decimal(refund_amount),
            channel_slug=payment.order.channel.slug,
        )

    assert e._excinfo[1].message == error


def test_refund_gateway_error(payment_txn_captured, monkeypatch):
    monkeypatch.setattr(
        "saleor.payment.gateways.dummy_credit_card.dummy_success", lambda: False
    )
    payment = payment_txn_captured
    payment.gateway = "mirumee.payments.dummy_credit_card"
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = Decimal("80.00")
    payment.save()
    with pytest.raises(PaymentError):
        gateway.refund(
            payment=payment,
            manager=get_plugins_manager(allow_replica=False),
            amount=Decimal("80.00"),
            channel_slug=payment.order.channel.slug,
        )

    payment.refresh_from_db()
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.REFUND
    assert not txn.is_success
    assert txn.payment == payment
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.captured_amount == Decimal("80.00")


@pytest.mark.parametrize("token", ["111", PREAUTHORIZED_TOKENS[1]])
def test_process_payment_success(token, payment_dummy_credit_card):
    # when
    txn = gateway.process_payment(
        payment=payment_dummy_credit_card,
        token=token,
        manager=get_plugins_manager(allow_replica=False),
        channel_slug=payment_dummy_credit_card.order.channel.slug,
    )

    # then
    assert txn.is_success
    assert txn.payment == payment_dummy_credit_card
    assert txn.kind == TransactionKind.CAPTURE
    assert not txn.error
    payment_dummy_credit_card.refresh_from_db()
    assert payment_dummy_credit_card.is_active


@pytest.mark.parametrize(("token", "error"), list(TOKEN_VALIDATION_MAPPING.items()))
def test_process_payment_failed(token, error, payment_dummy_credit_card):
    # when
    with pytest.raises(PaymentError) as e:
        gateway.process_payment(
            payment=payment_dummy_credit_card,
            token=token,
            manager=get_plugins_manager(allow_replica=False),
            channel_slug=payment_dummy_credit_card.order.channel.slug,
        )

    assert e._excinfo[1].message == error


def test_refund_method_error(dummy_payment_data, dummy_gateway_config, monkeypatch):
    # given
    monkeypatch.setattr(
        "saleor.payment.gateways.dummy_credit_card.dummy_success", lambda: False
    )

    # when
    response = refund(dummy_payment_data, dummy_gateway_config)

    # then
    assert not response.is_success
    assert response.kind == TransactionKind.REFUND
    assert response.error == "Unable to process refund"


def test_process_payment_pre_authorized(
    payment_dummy_credit_card, dummy_gateway_config, monkeypatch
):
    # given
    token = PREAUTHORIZED_TOKENS[1]
    dummy_gateway_config.auto_capture = False
    monkeypatch.setattr(
        "saleor.payment.gateways.dummy_credit_card.plugin."
        "DummyCreditCardGatewayPlugin._get_gateway_config",
        lambda _: dummy_gateway_config,
    )

    # when
    txn = gateway.process_payment(
        payment=payment_dummy_credit_card,
        token=token,
        manager=get_plugins_manager(allow_replica=False),
        channel_slug=payment_dummy_credit_card.order.channel.slug,
    )

    # then
    assert txn.is_success
    assert txn.payment == payment_dummy_credit_card
    assert txn.kind == TransactionKind.AUTH
    assert not txn.error
    payment_dummy_credit_card.refresh_from_db()
    assert payment_dummy_credit_card.is_active


def test_process_payment_pre_authorized_and_capture(
    payment_dummy_credit_card, dummy_gateway_config, monkeypatch
):
    # given
    token = PREAUTHORIZED_TOKENS[1]
    dummy_gateway_config.auto_capture = True
    monkeypatch.setattr(
        "saleor.payment.gateways.dummy_credit_card.plugin."
        "DummyCreditCardGatewayPlugin._get_gateway_config",
        lambda _: dummy_gateway_config,
    )

    # when
    txn = gateway.process_payment(
        payment=payment_dummy_credit_card,
        token=token,
        manager=get_plugins_manager(allow_replica=False),
        channel_slug=payment_dummy_credit_card.order.channel.slug,
    )

    # then
    assert txn.is_success
    assert txn.payment == payment_dummy_credit_card
    assert txn.kind == TransactionKind.CAPTURE
    assert not txn.error
    payment_dummy_credit_card.refresh_from_db()
    assert payment_dummy_credit_card.is_active


def test_process_payment_pre_authorized_and_capture_error(
    payment_dummy_credit_card, dummy_gateway_config, monkeypatch
):
    # given
    token = TOKEN_EXPIRED
    dummy_gateway_config.auto_capture = True
    monkeypatch.setattr(
        "saleor.payment.gateways.dummy_credit_card.plugin."
        "DummyCreditCardGatewayPlugin._get_gateway_config",
        lambda _: dummy_gateway_config,
    )

    # when
    with pytest.raises(PaymentError) as e:
        gateway.process_payment(
            payment=payment_dummy_credit_card,
            token=token,
            manager=get_plugins_manager(allow_replica=False),
            channel_slug=payment_dummy_credit_card.order.channel.slug,
        )

    assert e._excinfo[1].message == TOKEN_VALIDATION_MAPPING[token]


@pytest.mark.parametrize(("token", "error"), list(TOKEN_VALIDATION_MAPPING.items()))
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
