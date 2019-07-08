from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured

from saleor.order.events import OrderEvents, OrderEventsEmails
from saleor.payment import (
    ChargeStatus,
    GatewayError,
    OperationType,
    PaymentError,
    TransactionKind,
    get_payment_gateway,
)
from saleor.payment.interface import GatewayConfig, GatewayResponse, TokenConfig
from saleor.payment.models import Payment
from saleor.payment.utils import (
    ALLOWED_GATEWAY_KINDS,
    call_gateway,
    clean_authorize,
    clean_capture,
    clean_mark_order_as_paid,
    create_payment,
    create_payment_information,
    create_transaction,
    gateway_authorize,
    gateway_capture,
    gateway_get_client_token,
    gateway_process_payment,
    gateway_refund,
    gateway_void,
    handle_fully_paid_order,
    mark_order_as_paid,
    require_active_payment,
    validate_gateway_response,
)

NOT_ACTIVE_PAYMENT_ERROR = "This payment is no longer active."
EXAMPLE_ERROR = "Example dummy error"


@pytest.fixture
def gateway_response(settings):
    return GatewayResponse(
        is_success=True,
        transaction_id="transaction-token",
        amount=Decimal(14.50),
        currency=settings.DEFAULT_CURRENCY,
        kind=TransactionKind.CAPTURE,
        error=None,
        raw_response={
            "credit_card_four": "1234",
            "transaction-id": "transaction-token",
        },
    )


@pytest.fixture
def transaction_data(payment_dummy, gateway_response):
    return {
        "payment": payment_dummy,
        "payment_information": create_payment_information(
            payment_dummy, "payment-token"
        ),
        "kind": TransactionKind.CAPTURE,
        "gateway_response": gateway_response,
    }


@pytest.fixture
def gateway_config():
    return GatewayConfig(
        gateway_name="dummy",
        auto_capture=True,
        template_path="template.html",
        connection_params={"secret-key": "nobodylikesspanishinqusition"},
    )


@pytest.fixture
def transaction_token():
    return "transaction-token"


@pytest.fixture
def dummy_response(payment_dummy, transaction_data, transaction_token):
    return GatewayResponse(
        is_success=True,
        transaction_id=transaction_token,
        error=EXAMPLE_ERROR,
        amount=payment_dummy.total,
        currency=payment_dummy.currency,
        kind=TransactionKind.AUTH,
        raw_response=None,
    )


def test_get_payment_gateway_not_allowed_checkout_choice(settings):
    gateway = "example-gateway"
    settings.CHECKOUT_PAYMENT_GATEWAYS = {}
    with pytest.raises(ValueError):
        get_payment_gateway(gateway)


def test_get_payment_gateway_non_existing_name(settings):
    gateway = "example-gateway"
    settings.CHECKOUT_PAYMENT_GATEWAYS = {gateway: "Example gateway"}
    with pytest.raises(ImproperlyConfigured):
        get_payment_gateway(gateway)


def test_get_payment_gateway(settings):
    gateway_name = list(settings.PAYMENT_GATEWAYS.keys())[0]
    gateway = settings.PAYMENT_GATEWAYS[gateway_name]
    gateway_module, gateway_config = get_payment_gateway(gateway_name)
    assert gateway_module.__name__ == gateway["module"]
    assert gateway_config.connection_params == gateway["config"]["connection_params"]
    assert gateway_config.auto_capture == gateway["config"]["auto_capture"]


@patch("saleor.order.emails.send_payment_confirmation.delay")
def test_handle_fully_paid_order_no_email(mock_send_payment_confirmation, order):
    order.user = None
    order.user_email = ""

    handle_fully_paid_order(order)
    event = order.events.get()
    assert event.type == OrderEvents.ORDER_FULLY_PAID
    assert not mock_send_payment_confirmation.called


@patch("saleor.order.emails.send_payment_confirmation.delay")
def test_handle_fully_paid_order(mock_send_payment_confirmation, order):
    handle_fully_paid_order(order)
    event_order_paid, event_email_sent = order.events.all()
    assert event_order_paid.type == OrderEvents.ORDER_FULLY_PAID

    assert event_email_sent.type == OrderEvents.EMAIL_SENT
    assert event_email_sent.parameters == {
        "email": order.get_user_current_email(),
        "email_type": OrderEventsEmails.PAYMENT,
    }

    mock_send_payment_confirmation.assert_called_once_with(order.pk)


def test_require_active_payment():
    @require_active_payment
    def test_function(_payment, *_args, **_kwargs):
        return True

    payment = Mock(is_active=True)
    test_function(payment)

    non_active_payment = Mock(is_active=False)
    with pytest.raises(PaymentError):
        test_function(non_active_payment)


def test_create_payment(address, settings):
    data = {
        "gateway": settings.DUMMY,
        "payment_token": "token",
        "total": 10,
        "currency": settings.DEFAULT_CURRENCY,
        "email": "test@example.com",
        "billing_address": address,
        "customer_ip_address": "127.0.0.1",
    }
    payment = create_payment(**data)
    assert payment.gateway == settings.DUMMY

    same_payment = create_payment(**data)
    assert payment == same_payment


def test_mark_as_paid(admin_user, draft_order):
    mark_order_as_paid(draft_order, admin_user)
    payment = draft_order.payments.last()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.captured_amount == draft_order.total.gross.amount
    assert draft_order.events.last().type == (OrderEvents.ORDER_MARKED_AS_PAID)


def test_clean_mark_order_as_paid(payment_txn_preauth):
    order = payment_txn_preauth.order
    with pytest.raises(PaymentError):
        clean_mark_order_as_paid(order)


def test_create_transaction(transaction_data):
    txn = create_transaction(**transaction_data)

    assert txn.payment == transaction_data["payment"]
    gateway_response = transaction_data["gateway_response"]
    assert txn.kind == gateway_response.kind
    assert txn.amount == gateway_response.amount
    assert txn.currency == gateway_response.currency
    assert txn.token == gateway_response.transaction_id
    assert txn.is_success == gateway_response.is_success
    assert txn.gateway_response == gateway_response.raw_response


def test_create_transaction_no_gateway_response(transaction_data):
    transaction_data.pop("gateway_response")
    txn = create_transaction(**transaction_data)
    assert txn.gateway_response == {}


@patch("saleor.payment.utils.get_payment_gateway")
def test_gateway_get_client_token(get_payment_gateway_mock, gateway_config):
    get_client_token_mock = Mock(return_value="client-token")
    get_payment_gateway_mock.return_value = (
        Mock(get_client_token=get_client_token_mock),
        gateway_config,
    )

    token = gateway_get_client_token("some-gateway")

    assert token == "client-token"
    get_client_token_mock.assert_called_once_with(
        config=gateway_config, token_config=TokenConfig()
    )


def test_gateway_get_client_token_not_allowed_gateway(settings):
    gateway = "example-gateway"
    settings.CHECKOUT_PAYMENT_GATEWAYS = {}
    with pytest.raises(ValueError):
        gateway_get_client_token(gateway)


def test_gateway_get_client_token_not_existing_gateway(settings):
    gateway = "example-gateway"
    settings.CHECKOUT_PAYMENT_GATEWAYS = {gateway: "Example gateway"}
    with pytest.raises(ImproperlyConfigured):
        gateway_get_client_token(gateway)


@pytest.mark.parametrize(
    "func", [gateway_authorize, gateway_capture, gateway_refund, gateway_void]
)
def test_payment_needs_to_be_active_for_any_action(func, payment_dummy):
    payment_dummy.is_active = False
    with pytest.raises(PaymentError) as exc:
        func(payment_dummy, "token")
    assert exc.value.message == NOT_ACTIVE_PAYMENT_ERROR


@patch("saleor.payment.utils.get_payment_gateway")
def test_gateway_process_payment(
    mock_get_payment_gateway,
    payment_txn_preauth,
    gateway_config,
    transaction_token,
    dummy_response,
):
    payment_token = transaction_token
    payment = payment_txn_preauth
    mock_process_payment = Mock(return_value=dummy_response)
    mock_get_payment_gateway.return_value = (
        Mock(process_payment=mock_process_payment),
        gateway_config,
    )

    payment_info = create_payment_information(payment, payment_token)
    gateway_process_payment(payment, payment_token)

    mock_get_payment_gateway.assert_called_with(payment.gateway)
    mock_process_payment.assert_called_once_with(
        payment_information=payment_info, config=gateway_config
    )


@patch("saleor.payment.utils.get_payment_gateway")
def test_gateway_authorize(
    mock_get_payment_gateway,
    payment_txn_preauth,
    gateway_config,
    transaction_token,
    dummy_response,
):
    payment = payment_txn_preauth
    payment_token = transaction_token

    mock_authorize = Mock(return_value=dummy_response)
    mock_get_payment_gateway.return_value = (
        Mock(authorize=mock_authorize),
        gateway_config,
    )

    payment_info = create_payment_information(payment, payment_token)
    gateway_authorize(payment, payment_token)

    mock_get_payment_gateway.assert_called_once_with(payment.gateway)
    mock_authorize.assert_called_once_with(
        payment_information=payment_info, config=gateway_config
    )


@patch("saleor.payment.utils.get_payment_gateway")
def test_gateway_authorize_failed(
    mock_get_payment_gateway,
    payment_txn_preauth,
    gateway_config,
    transaction_token,
    dummy_response,
):
    payment_token = transaction_token
    txn = payment_txn_preauth.transactions.first()
    txn.is_success = False
    payment = payment_txn_preauth

    dummy_response.is_success = False
    mock_authorize = Mock(return_value=dummy_response)
    mock_get_payment_gateway.return_value = (
        Mock(authorize=mock_authorize),
        gateway_config,
    )
    with pytest.raises(PaymentError) as exc:
        gateway_authorize(payment, payment_token)
    assert exc.value.message == EXAMPLE_ERROR


def test_gateway_authorize_errors(payment_dummy):
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    with pytest.raises(PaymentError) as exc:
        gateway_authorize(payment_dummy, "payment-token")
    assert exc.value.message == ("Charged transactions cannot be authorized again.")


@patch("saleor.payment.utils.handle_fully_paid_order")
@patch("saleor.payment.utils.get_payment_gateway")
def test_gateway_capture(
    mock_get_payment_gateway,
    mock_handle_fully_paid_order,
    payment_txn_preauth,
    gateway_config,
    dummy_response,
):
    payment = payment_txn_preauth
    gateway_config.auto_capture = True
    assert not payment.captured_amount
    amount = payment.total

    dummy_response.kind = TransactionKind.CAPTURE
    mock_capture = Mock(return_value=dummy_response)
    mock_get_payment_gateway.return_value = (Mock(capture=mock_capture), gateway_config)

    payment_info = create_payment_information(payment, "", amount)
    gateway_capture(payment, amount)

    mock_capture.assert_called_once_with(
        payment_information=payment_info, config=gateway_config
    )

    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.captured_amount == payment.total
    mock_handle_fully_paid_order.assert_called_once_with(payment.order)


@patch("saleor.payment.utils.handle_fully_paid_order")
@patch("saleor.payment.utils.get_payment_gateway")
def test_gateway_capture_partial_capture(
    mock_get_payment_gateway,
    mock_handle_fully_paid_order,
    payment_txn_preauth,
    gateway_config,
    settings,
    dummy_response,
):
    payment = payment_txn_preauth
    amount = payment.total * Decimal("0.5")
    txn = payment.transactions.first()
    txn.amount = amount
    txn.currency = settings.DEFAULT_CURRENCY

    dummy_response.kind = TransactionKind.CAPTURE
    dummy_response.amount = amount
    mock_capture = Mock(return_value=dummy_response)
    mock_get_payment_gateway.return_value = (Mock(capture=mock_capture), gateway_config)

    gateway_capture(payment, amount)

    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.PARTIALLY_CHARGED
    assert payment.captured_amount == amount
    assert payment.currency == settings.DEFAULT_CURRENCY
    assert not mock_handle_fully_paid_order.called


@patch("saleor.payment.utils.handle_fully_paid_order")
@patch("saleor.payment.utils.get_payment_gateway")
def test_gateway_capture_failed(
    mock_get_payment_gateway,
    mock_handle_fully_paid_order,
    payment_txn_preauth,
    gateway_config,
    dummy_response,
):
    txn = payment_txn_preauth.transactions.first()
    txn.is_success = False

    payment = payment_txn_preauth
    amount = payment.total

    dummy_response.is_success = False
    dummy_response.kind = TransactionKind.CAPTURE
    mock_capture = Mock(return_value=dummy_response)
    mock_get_payment_gateway.return_value = (Mock(capture=mock_capture), gateway_config)
    with pytest.raises(PaymentError) as exc:
        gateway_capture(payment, amount)
    assert exc.value.message == EXAMPLE_ERROR
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert not payment.captured_amount
    assert not mock_handle_fully_paid_order.called


def test_gateway_capture_errors(payment_txn_preauth):
    with pytest.raises(PaymentError) as exc:
        gateway_capture(payment_txn_preauth, Decimal("0"))
    assert exc.value.message == "Amount should be a positive number."

    payment_txn_preauth.charge_status = ChargeStatus.FULLY_REFUNDED
    with pytest.raises(PaymentError) as exc:
        gateway_capture(payment_txn_preauth, Decimal("10"))
    assert exc.value.message == "This payment cannot be captured."

    payment_txn_preauth.charge_status = ChargeStatus.NOT_CHARGED
    with pytest.raises(PaymentError) as exc:
        gateway_capture(payment_txn_preauth, Decimal("1000000"))
    assert exc.value.message == ("Unable to charge more than un-captured amount.")


@patch("saleor.payment.utils.handle_fully_paid_order")
@patch("saleor.payment.utils.get_payment_gateway")
def test_gateway_capture_partial_charge(
    mock_get_payment_gateway,
    mock_handle_fully_paid_order,
    payment_txn_preauth,
    gateway_config,
    transaction_token,
    settings,
    dummy_response,
):
    payment = payment_txn_preauth
    amount = payment.total * Decimal("0.5")
    txn = payment.transactions.first()
    txn.amount = amount
    txn.currency = settings.DEFAULT_CURRENCY

    dummy_response.kind = TransactionKind.CAPTURE
    dummy_response.amount = amount
    mock_charge = Mock(return_value=dummy_response)
    mock_get_payment_gateway.return_value = (Mock(capture=mock_charge), gateway_config)

    gateway_capture(payment, amount)

    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.PARTIALLY_CHARGED
    assert payment.captured_amount == amount
    assert payment.currency == settings.DEFAULT_CURRENCY
    assert not mock_handle_fully_paid_order.called


@patch("saleor.payment.utils.handle_fully_paid_order")
@patch("saleor.payment.utils.get_payment_gateway")
def test_gateway_charge_failed(
    mock_get_payment_gateway,
    mock_handle_fully_paid_order,
    payment_txn_preauth,
    gateway_config,
    transaction_token,
    dummy_response,
):
    txn = payment_txn_preauth.transactions.first()
    txn.is_success = False

    payment = payment_txn_preauth
    amount = payment.total

    dummy_response.is_success = False
    dummy_response.kind = TransactionKind.CAPTURE
    mock_charge = Mock(return_value=dummy_response)
    mock_get_payment_gateway.return_value = (Mock(capture=mock_charge), gateway_config)
    with pytest.raises(PaymentError) as exc:
        gateway_capture(payment, amount)
    assert exc.value.message == EXAMPLE_ERROR
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert not payment.captured_amount
    assert not mock_handle_fully_paid_order.called


def test_gateway_charge_errors(payment_dummy, transaction_token, settings):
    payment = payment_dummy
    gateway_authorize(payment, transaction_token)
    with pytest.raises(PaymentError) as exc:
        gateway_capture(payment, Decimal("0"))
    assert exc.value.message == "Amount should be a positive number."

    payment.charge_status = ChargeStatus.FULLY_REFUNDED
    with pytest.raises(PaymentError) as exc:
        gateway_capture(payment, Decimal("10"))
    assert exc.value.message == "This payment cannot be captured."

    payment.charge_status = ChargeStatus.NOT_CHARGED
    with pytest.raises(PaymentError) as exc:
        gateway_capture(payment, Decimal("1000000"))
    assert exc.value.message == ("Unable to charge more than un-captured amount.")


@patch("saleor.payment.utils.get_payment_gateway")
def test_gateway_void(
    mock_get_payment_gateway, payment_txn_preauth, gateway_config, dummy_response
):
    txn = payment_txn_preauth.transactions.first()
    payment = payment_txn_preauth
    assert payment.is_active

    dummy_response.kind = TransactionKind.VOID
    mock_void = Mock(return_value=dummy_response)
    mock_get_payment_gateway.return_value = (Mock(void=mock_void), gateway_config)

    payment_info = create_payment_information(payment, txn.token)
    gateway_void(payment)

    mock_get_payment_gateway.assert_called_once_with(payment.gateway)
    mock_void.assert_called_once_with(
        payment_information=payment_info, config=gateway_config
    )

    payment.refresh_from_db()
    assert payment.is_active is False


@patch("saleor.payment.utils.get_payment_gateway")
def test_gateway_void_failed(
    mock_get_payment_gateway, payment_txn_preauth, gateway_config, dummy_response
):
    txn = payment_txn_preauth.transactions.first()
    txn.is_success = False
    payment = payment_txn_preauth

    dummy_response.kind = TransactionKind.VOID
    dummy_response.is_success = False
    mock_void = Mock(return_value=dummy_response)
    mock_get_payment_gateway.return_value = (Mock(void=mock_void), gateway_config)
    with pytest.raises(PaymentError) as exc:
        gateway_void(payment)
    assert exc.value.message == EXAMPLE_ERROR

    payment.refresh_from_db()
    assert payment.is_active


def test_gateway_void_errors(payment_dummy):
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    with pytest.raises(PaymentError) as exc:
        gateway_void(payment_dummy)
    assert exc.value.message == "Only pre-authorized transactions can be voided."


@patch("saleor.payment.utils.get_payment_gateway")
def test_gateway_refund(
    mock_get_payment_gateway, payment_txn_captured, gateway_config, dummy_response
):
    txn = payment_txn_captured.transactions.first()
    payment = payment_txn_captured
    amount = payment.total

    dummy_response.kind = TransactionKind.REFUND
    mock_refund = Mock(return_value=dummy_response)
    mock_get_payment_gateway.return_value = (Mock(refund=mock_refund), gateway_config)

    payment_info = create_payment_information(payment, txn.token, amount)
    gateway_refund(payment, amount)

    mock_get_payment_gateway.assert_called_once_with(payment.gateway)
    mock_refund.assert_called_once_with(
        payment_information=payment_info, config=gateway_config
    )

    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_REFUNDED
    assert not payment.captured_amount


@patch("saleor.payment.utils.get_payment_gateway")
def test_gateway_refund_partial_refund(
    mock_get_payment_gateway,
    payment_txn_captured,
    gateway_config,
    settings,
    dummy_response,
):
    payment = payment_txn_captured
    amount = payment.total * Decimal("0.5")
    txn = payment_txn_captured.transactions.first()
    txn.amount = amount
    txn.currency = settings.DEFAULT_CURRENCY

    dummy_response.kind = TransactionKind.REFUND
    dummy_response.amount = amount
    mock_refund = Mock(return_value=dummy_response)
    mock_get_payment_gateway.return_value = (Mock(refund=mock_refund), gateway_config)

    gateway_refund(payment, amount)

    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.PARTIALLY_REFUNDED
    assert payment.captured_amount == payment.total - amount


@patch("saleor.payment.utils.get_payment_gateway")
def test_gateway_refund_failed(
    mock_get_payment_gateway,
    payment_txn_captured,
    gateway_config,
    settings,
    dummy_response,
):
    txn = payment_txn_captured.transactions.first()
    payment = payment_txn_captured
    captured_before = payment.captured_amount
    txn.is_success = False

    dummy_response.kind = TransactionKind.REFUND
    dummy_response.is_success = False
    mock_refund = Mock(return_value=dummy_response)
    mock_get_payment_gateway.return_value = (Mock(refund=mock_refund), gateway_config)

    with pytest.raises(PaymentError) as exc:
        gateway_refund(payment, Decimal("10.00"))
    assert exc.value.message == EXAMPLE_ERROR
    payment.refresh_from_db()
    assert payment.captured_amount == captured_before


def test_gateway_refund_errors(payment_txn_captured):
    payment = payment_txn_captured
    with pytest.raises(PaymentError) as exc:
        gateway_refund(payment, Decimal("1000000"))
    assert exc.value.message == "Cannot refund more than captured"

    with pytest.raises(PaymentError) as exc:
        gateway_refund(payment, Decimal("0"))
    assert exc.value.message == "Amount should be a positive number."

    payment.charge_status = ChargeStatus.NOT_CHARGED
    with pytest.raises(PaymentError) as exc:
        gateway_refund(payment, Decimal("1"))
    assert exc.value.message == "This payment cannot be refunded."


def test_clean_authorize():
    payment = Mock(can_authorize=Mock(return_value=True))
    clean_authorize(payment)

    payment = Mock(can_authorize=Mock(return_value=False))
    with pytest.raises(PaymentError):
        clean_authorize(payment)


def test_clean_capture():
    # Amount should be a positive number
    payment = Mock()
    amount = Decimal("0.00")
    with pytest.raises(PaymentError):
        clean_capture(payment, amount)

    # Payment cannot be captured
    payment = Mock(can_capture=Mock(return_value=False))
    amount = Decimal("1.00")
    with pytest.raises(PaymentError):
        clean_capture(payment, amount)

    # Amount is larger than payment's total
    payment = Mock(
        can_capture=Mock(return_value=True),
        total=Decimal("1.00"),
        captured_amount=Decimal("0.00"),
    )
    amount = Decimal("2.00")
    with pytest.raises(PaymentError):
        clean_capture(payment, amount)

    amount = Decimal("2.00")
    payment = Mock(
        can_capture=Mock(return_value=True),
        total=amount,
        captured_amount=Decimal("0.00"),
    )
    clean_capture(payment, amount)


def test_can_authorize(payment_dummy: Payment):
    assert payment_dummy.charge_status == ChargeStatus.NOT_CHARGED

    payment_dummy.is_active = False
    assert not payment_dummy.can_authorize()

    payment_dummy.is_active = True
    assert payment_dummy.can_authorize()

    payment_dummy.charge_status = ChargeStatus.PARTIALLY_CHARGED
    assert not payment_dummy.can_authorize()

    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    assert not payment_dummy.can_authorize()


def test_can_capture(payment_txn_preauth: Payment):
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED

    payment_txn_preauth.is_active = False
    assert not payment_txn_preauth.can_capture()

    payment_txn_preauth.is_active = True
    assert payment_txn_preauth.can_capture()

    payment_txn_preauth.charge_status = ChargeStatus.PARTIALLY_CHARGED
    assert not payment_txn_preauth.can_capture()

    payment_txn_preauth.charge_status = ChargeStatus.FULLY_CHARGED
    assert not payment_txn_preauth.can_capture()

    payment_txn_preauth.captured_amount = 0
    payment_txn_preauth.transactions.all().delete()
    assert not payment_txn_preauth.can_capture()


def test_can_void(payment_txn_preauth: Payment):
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED

    payment_txn_preauth.is_active = False
    assert not payment_txn_preauth.can_void()

    payment_txn_preauth.is_active = True
    assert payment_txn_preauth.can_void()

    payment_txn_preauth.charge_status = ChargeStatus.PARTIALLY_CHARGED
    assert not payment_txn_preauth.can_void()

    payment_txn_preauth.charge_status = ChargeStatus.FULLY_CHARGED
    assert not payment_txn_preauth.can_void()

    payment_txn_preauth.charge_status = ChargeStatus.NOT_CHARGED
    payment_txn_preauth.transactions.all().delete()
    assert not payment_txn_preauth.can_void()


def test_can_refund(payment_dummy: Payment):
    assert payment_dummy.charge_status == ChargeStatus.NOT_CHARGED

    payment_dummy.is_active = False
    assert not payment_dummy.can_refund()

    payment_dummy.is_active = True
    assert not payment_dummy.can_refund()

    payment_dummy.charge_status = ChargeStatus.PARTIALLY_CHARGED
    assert payment_dummy.can_refund()

    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    assert payment_dummy.can_refund()


def test_payment_get_authorized_amount(payment_txn_preauth):
    payment = payment_txn_preauth

    authorized_amount = payment.transactions.first().amount
    assert payment.get_authorized_amount().amount == authorized_amount
    assert payment.order.total_authorized.amount == authorized_amount

    payment.transactions.create(
        amount=payment.total,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )
    assert payment.get_authorized_amount().amount == Decimal(0)

    payment.transactions.all().delete()
    assert payment.get_authorized_amount().amount == Decimal(0)


def test_validate_gateway_response(gateway_response):
    validate_gateway_response(gateway_response)


def test_validate_gateway_response_incorrect_transaction_kind(gateway_response):
    gateway_response.kind = "incorrect-kind"

    with pytest.raises(GatewayError) as e:
        validate_gateway_response(gateway_response)

    assert str(e.value) == (
        "Gateway response kind must be one of {}".format(sorted(ALLOWED_GATEWAY_KINDS))
    )


def test_validate_gateway_response_not_json_serializable(gateway_response):
    class CustomClass(object):
        pass

    gateway_response.raw_response = CustomClass()

    with pytest.raises(GatewayError) as e:
        validate_gateway_response(gateway_response)

    assert str(e.value) == "Gateway response needs to be json serializable"


@patch("saleor.payment.utils.get_payment_gateway")
def test_call_gateway_invalid_response(mock_get_payment_gateway, payment_dummy):
    mock_get_payment_gateway.return_value = (
        Mock(auth=Mock(return_value=("wrong", "response"))),
        {},
    )

    with pytest.raises(PaymentError) as e:
        call_gateway(
            operation_type=OperationType.AUTH,
            payment=payment_dummy,
            payment_token="token",
        )
    assert str(e.value) == "Gateway response validation failed"


@patch("saleor.payment.utils.get_payment_gateway")
def test_call_gateway_function_not_implemented(mock_get_payment_gateway, payment_dummy):
    class CustomClass:
        pass

    mock_get_payment_gateway.return_value = (CustomClass(), {})

    with pytest.raises(PaymentError) as e:
        call_gateway(
            operation_type=OperationType.AUTH,
            payment=payment_dummy,
            payment_token="token",
        )
    assert str(e.value) == "Gateway doesn't implement AUTH operation"


@patch("saleor.payment.utils.get_payment_gateway")
def test_call_gateway_generic_error(mock_get_payment_gateway, payment_dummy):
    mock_get_payment_gateway.return_value = (
        Mock(authorize=Mock(side_effect=Exception("something went wrong"))),
        {},
    )

    with pytest.raises(PaymentError) as e:
        call_gateway(
            operation_type=OperationType.AUTH,
            payment=payment_dummy,
            payment_token="token",
        )
    assert str(e.value) == "Gateway encountered an error"
