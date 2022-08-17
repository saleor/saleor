import uuid
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import AnonymousUser

from ...checkout.calculations import checkout_total
from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...core.prices import quantize_price
from ...plugins.manager import PluginsManager, get_plugins_manager
from .. import (
    ChargeStatus,
    GatewayError,
    PaymentError,
    StorePaymentMethod,
    TransactionKind,
    gateway,
)
from ..error_codes import PaymentErrorCode
from ..interface import GatewayResponse, PaymentMethodInfo, TransactionData
from ..models import Payment
from ..utils import (
    ALLOWED_GATEWAY_KINDS,
    clean_authorize,
    clean_capture,
    create_payment,
    create_payment_information,
    create_transaction,
    is_currency_supported,
    payment_owned_by_user,
    update_payment,
    validate_gateway_response,
)

NOT_ACTIVE_PAYMENT_ERROR = "This payment is no longer active."
EXAMPLE_ERROR = "Example dummy error"


@pytest.fixture
def payment_method_details():
    return PaymentMethodInfo(
        last_4="1234",
        exp_year=2020,
        exp_month=8,
        brand="visa",
        name="Joe Doe",
        type="test",
    )


@pytest.fixture
def gateway_response(settings, payment_method_details):
    return GatewayResponse(
        is_success=True,
        action_required=False,
        transaction_id="transaction-token",
        amount=Decimal(14.50),
        currency="USD",
        kind=TransactionKind.CAPTURE,
        error=None,
        raw_response={
            "credit_card_four": "1234",
            "transaction-id": "transaction-token",
        },
        payment_method_info=payment_method_details,
        psp_reference="test_reference",
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
def transaction_data_long_error_message(payment_dummy):
    error_msg = "This is very very long response from payment gateway. " * 10
    return {
        "payment": payment_dummy,
        "payment_information": create_payment_information(
            payment_dummy, "payment-token"
        ),
        "error_msg": error_msg,
        "kind": TransactionKind.CAPTURE_FAILED,
    }


@pytest.fixture
def transaction_token():
    return "transaction-token"


@pytest.fixture
def dummy_response(payment_dummy, transaction_token, payment_method_details):
    return GatewayResponse(
        is_success=True,
        action_required=False,
        transaction_id=transaction_token,
        error=EXAMPLE_ERROR,
        amount=payment_dummy.total,
        currency=payment_dummy.currency,
        kind=TransactionKind.AUTH,
        raw_response=None,
        payment_method_info=payment_method_details,
    )


def test_create_payment(checkout_with_item, address):
    checkout_with_item.billing_address = address
    checkout_with_item.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    total = checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    data = {
        "gateway": "Dummy",
        "payment_token": "token",
        "total": total.gross.amount,
        "currency": checkout_with_item.currency,
        "email": "test@example.com",
        "customer_ip_address": "127.0.0.1",
        "checkout": checkout_with_item,
    }
    payment = create_payment(**data)
    assert payment.gateway == "Dummy"
    assert payment.store_payment_method == StorePaymentMethod.NONE

    same_payment = create_payment(**data)
    assert payment == same_payment


def test_create_payment_requires_order_or_checkout(settings):
    data = {
        "gateway": "Dummy",
        "payment_token": "token",
        "total": 10,
        "currency": "USD",
        "email": "test@example.com",
    }
    with pytest.raises(TypeError) as e:
        create_payment(**data)
    assert e.value.args[0] == "Must provide checkout or order to create a payment."


def test_create_payment_from_checkout_requires_billing_address(checkout_with_item):
    checkout_with_item.billing_address = None
    checkout_with_item.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    total = checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=None
    )

    data = {
        "gateway": "Dummy",
        "payment_token": "token",
        "total": total.gross.amount,
        "currency": checkout_with_item.currency,
        "email": "test@example.com",
        "checkout": checkout_with_item,
    }
    with pytest.raises(PaymentError) as e:
        create_payment(**data)
    assert e.value.code == PaymentErrorCode.BILLING_ADDRESS_NOT_SET.value


def test_create_payment_from_order_requires_billing_address(draft_order):
    draft_order.billing_address = None
    draft_order.save()

    data = {
        "gateway": "Dummy",
        "payment_token": "token",
        "total": draft_order.total.gross.amount,
        "currency": draft_order.currency,
        "email": "test@example.com",
        "order": draft_order,
    }
    with pytest.raises(PaymentError) as e:
        create_payment(**data)
    assert e.value.code == PaymentErrorCode.BILLING_ADDRESS_NOT_SET.value


def test_create_payment_information_for_checkout_payment(address, checkout_with_item):
    checkout_with_item.billing_address = address
    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    total = checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    data = {
        "gateway": "Dummy",
        "payment_token": "token",
        "total": total.gross.amount,
        "currency": checkout_with_item.currency,
        "email": "test@example.com",
        "customer_ip_address": "127.0.0.1",
        "checkout": checkout_with_item,
    }

    payment = create_payment(**data)
    payment_data = create_payment_information(payment, "token", payment.total)

    billing = payment_data.billing
    shipping = payment_data.shipping
    assert billing
    assert billing.first_name == address.first_name
    assert billing.last_name == address.last_name
    assert billing.street_address_1 == address.street_address_1
    assert billing.city == address.city
    assert shipping == billing


def test_create_payment_information_for_checkout_token(payment_dummy, checkout):
    payment_dummy.order = None
    payment_dummy.checkout = checkout
    payment_dummy.save(update_fields=["order", "checkout"])

    payment_info = create_payment_information(payment_dummy)
    assert payment_info.checkout_token == str(checkout.token)


def test_create_payment_information_for_checkout_token_from_order(payment_dummy, order):
    token = str(uuid.uuid4())
    order.checkout_token = token
    order.save(update_fields=["checkout_token"])
    payment_dummy.order = order
    payment_dummy.checkout = None
    payment_dummy.save(update_fields=["order", "checkout"])

    payment_info = create_payment_information(payment_dummy)
    assert payment_info.checkout_token == order.checkout_token == token


def test_create_payment_information_for_empty_payment(payment_dummy):
    payment_dummy.order = None
    payment_dummy.checkout = None
    payment_dummy.save(update_fields=["order", "checkout"])

    payment_info = create_payment_information(payment_dummy)
    assert payment_info.checkout_token == ""
    assert payment_info.checkout_metadata is None


def test_create_payment_information_for_checkout_metadata(payment_dummy, checkout):
    metadata = {"test_key": "test_val"}
    checkout.metadata = metadata
    checkout.save(update_fields=["metadata"])
    payment_dummy.order = None
    payment_dummy.checkout = checkout
    payment_dummy.save(update_fields=["order", "checkout"])

    payment_info = create_payment_information(payment_dummy)
    assert payment_info.checkout_metadata == metadata


def test_create_payment_information_for_payment_with_transactions(payment_dummy):
    # given
    payment_dummy.transactions.create(
        amount=payment_dummy.total,
        currency=payment_dummy.currency,
        kind=TransactionKind.AUTH,
        gateway_response={"status": "SUCCESS"},
        is_success=True,
    )

    # when
    payment_info = create_payment_information(payment_dummy)

    # then
    for transaction in payment_dummy.transactions.all():
        assert (
            TransactionData(
                token=transaction.token,
                is_success=transaction.is_success,
                kind=transaction.kind,
                gateway_response=transaction.gateway_response,
                amount={
                    "amount": str(
                        quantize_price(transaction.amount, transaction.currency)
                    ),
                    "currency": transaction.currency,
                },
            )
            in payment_info.transactions
        )


def test_create_payment_information_for_draft_order(draft_order):
    data = {
        "gateway": "Dummy",
        "payment_token": "token",
        "total": draft_order.total.gross.amount,
        "currency": draft_order.currency,
        "email": "test@example.com",
        "customer_ip_address": "127.0.0.1",
        "order": draft_order,
    }

    payment = create_payment(**data)
    payment_data = create_payment_information(payment, "token", payment.total)

    billing = payment_data.billing
    shipping = payment_data.shipping
    assert billing
    assert billing.first_name == draft_order.billing_address.first_name
    assert billing.last_name == draft_order.billing_address.last_name
    assert billing.street_address_1 == draft_order.billing_address.street_address_1
    assert billing.city == draft_order.billing_address.city
    assert shipping == billing


@pytest.mark.parametrize("store", ["NONE", "ON_SESSION", "OFF_SESSION"])
def test_create_payment_information_store(checkout_with_item, address, store):
    # given
    checkout_with_item.billing_address = address
    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    total = checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    data = {
        "gateway": "Dummy",
        "payment_token": "token",
        "total": total.gross.amount,
        "currency": checkout_with_item.currency,
        "email": "test@example.com",
        "customer_ip_address": "127.0.0.1",
        "checkout": checkout_with_item,
        "store_payment_method": store,
    }

    # when
    payment = create_payment(**data)
    payment_data = create_payment_information(payment, "token", payment.total)

    # then
    assert payment_data.store_payment_method == store


@pytest.mark.parametrize(
    "metadata", [{f"key{i}": f"value{i}" for i in range(5)}, {}, None]
)
def test_create_payment_information_metadata(checkout_with_item, address, metadata):
    # given
    checkout_with_item.billing_address = address
    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    total = checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    data = {
        "gateway": "Dummy",
        "payment_token": "token",
        "total": total.gross.amount,
        "currency": checkout_with_item.currency,
        "email": "test@example.com",
        "customer_ip_address": "127.0.0.1",
        "checkout": checkout_with_item,
        "metadata": metadata,
    }

    # when
    payment = create_payment(**data)
    payment_data = create_payment_information(payment, "token", payment.total)

    # then
    assert payment_data.payment_metadata == (metadata or {})


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


def test_create_transaction_long_error_message(transaction_data_long_error_message):
    transaction_data = transaction_data_long_error_message
    txn = create_transaction(**transaction_data)

    assert txn.payment == transaction_data["payment"]
    assert txn.error == transaction_data["error_msg"]


def test_create_transaction_no_gateway_response(transaction_data):
    transaction_data.pop("gateway_response")
    txn = create_transaction(**transaction_data)
    assert txn.gateway_response == {}


@patch.object(PluginsManager, "capture_payment")
@patch("saleor.order.actions.handle_fully_paid_order")
def test_gateway_charge_failed(
    mock_handle_fully_paid_order,
    mock_capture_payment,
    payment_txn_preauth,
    dummy_response,
):
    txn = payment_txn_preauth.transactions.first()
    txn.is_success = False

    payment = payment_txn_preauth
    amount = payment.total

    dummy_response.is_success = False
    dummy_response.kind = TransactionKind.CAPTURE
    mock_capture_payment.return_value = dummy_response
    with pytest.raises(PaymentError):
        gateway.capture(payment, get_plugins_manager(), amount)
    mock_capture_payment.assert_called_once()
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert not payment.captured_amount
    assert not mock_handle_fully_paid_order.called


def test_gateway_charge_errors(payment_dummy, transaction_token, settings):
    payment = payment_dummy
    gateway.authorize(
        payment,
        transaction_token,
        get_plugins_manager(),
        channel_slug=payment_dummy.order.channel.slug,
    )
    with pytest.raises(PaymentError) as exc:
        gateway.capture(
            payment,
            get_plugins_manager(),
            amount=Decimal("0"),
            channel_slug=payment_dummy.order.channel.slug,
        )
    assert exc.value.message == "Amount should be a positive number."

    payment.charge_status = ChargeStatus.FULLY_REFUNDED
    payment.save()
    with pytest.raises(PaymentError) as exc:
        gateway.capture(
            payment,
            get_plugins_manager(),
            amount=Decimal("10"),
            channel_slug=payment_dummy.order.channel.slug,
        )
    assert exc.value.message == "This payment cannot be captured."

    payment.charge_status = ChargeStatus.NOT_CHARGED
    payment.save()
    with pytest.raises(PaymentError) as exc:
        gateway.capture(
            payment,
            get_plugins_manager(),
            amount=Decimal("1000000"),
            channel_slug=payment_dummy.order.channel.slug,
        )
    assert exc.value.message == ("Unable to charge more than un-captured amount.")


def test_gateway_refund_errors(payment_txn_captured):
    payment = payment_txn_captured
    with pytest.raises(PaymentError) as exc:
        gateway.refund(
            payment,
            get_plugins_manager(),
            amount=Decimal("1000000"),
            channel_slug=payment_txn_captured.order.channel.slug,
        )
    assert exc.value.message == "Cannot refund more than captured."

    with pytest.raises(PaymentError) as exc:
        gateway.refund(
            payment,
            get_plugins_manager(),
            amount=Decimal("0"),
            channel_slug=payment_txn_captured.order.channel.slug,
        )
    assert exc.value.message == "Amount should be a positive number."

    payment.charge_status = ChargeStatus.NOT_CHARGED
    payment.save()
    with pytest.raises(PaymentError) as exc:
        gateway.refund(
            payment,
            get_plugins_manager(),
            amount=Decimal("1"),
            channel_slug=payment_txn_captured.order.channel.slug,
        )
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
    assert payment_txn_preauth.can_void()

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


@pytest.mark.parametrize(
    "currency, exp_response",
    [("EUR", True), ("USD", True), ("PLN", False)],
)
def test_is_currency_supported(
    currency, exp_response, dummy_gateway_config, monkeypatch, channel_USD
):
    # given
    manager = get_plugins_manager()
    dummy_gateway_config.supported_currencies = "USD, EUR"
    monkeypatch.setattr(
        "saleor.payment.gateways.dummy.plugin.DummyGatewayPlugin._get_gateway_config",
        lambda _: dummy_gateway_config,
    )

    # when
    response = is_currency_supported(currency, "mirumee.payments.dummy", manager)

    # then
    assert response == exp_response


def test_update_payment(gateway_response, payment_txn_captured):
    payment = payment_txn_captured

    update_payment(payment_txn_captured, gateway_response)

    payment.refresh_from_db()
    assert payment.psp_reference == gateway_response.psp_reference
    assert payment.cc_brand == gateway_response.payment_method_info.brand
    assert payment.cc_last_digits == gateway_response.payment_method_info.last_4
    assert payment.cc_exp_year == gateway_response.payment_method_info.exp_year
    assert payment.cc_exp_month == gateway_response.payment_method_info.exp_month
    assert payment.payment_method_type == gateway_response.payment_method_info.type


def test_payment_owned_by_user_from_order(payment, customer_user2):
    # given
    assert payment.checkout is None
    payment.order.user = customer_user2
    payment.order.save()

    # when
    is_owned = payment_owned_by_user(payment.pk, customer_user2)

    # then
    assert is_owned


def test_payment_owned_by_user_from_checkout(payment, checkout, customer_user2):
    # given
    checkout.user = customer_user2
    checkout.save()
    payment.checkout = checkout
    payment.order = None
    payment.save()

    # when
    is_owned = payment_owned_by_user(payment.pk, customer_user2)

    # then
    assert is_owned


def test_payment_is_not_owned_by_user_for_order(payment, customer_user2):
    # given
    assert payment.checkout is None
    assert payment.order.user != customer_user2

    # when
    is_owned = payment_owned_by_user(payment.pk, customer_user2)

    # then
    assert not is_owned


def test_payment_is_not_owned_by_user_for_checkout(payment, checkout, customer_user2):
    # given
    assert checkout.user != customer_user2
    payment.checkout = checkout
    payment.order = None
    payment.save()

    # when
    is_owned = payment_owned_by_user(payment.pk, customer_user2)

    # then
    assert not is_owned


def test_payment_owned_by_user_anonymous_user(payment):
    # given
    user = AnonymousUser()

    # when
    is_owned = payment_owned_by_user(payment.pk, user)

    # then
    assert not is_owned
