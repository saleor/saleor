from datetime import timedelta
from decimal import Decimal
from unittest import mock
from unittest.mock import ANY, Mock, patch

import pytest
from django.test import override_settings
from freezegun import freeze_time

from ...checkout.calculations import checkout_total
from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...plugins.manager import PluginsManager, get_plugins_manager
from .. import ChargeStatus, GatewayError, PaymentError, TransactionKind, gateway
from ..error_codes import PaymentErrorCode
from ..interface import GatewayResponse
from ..model_helpers import get_total_authorized
from ..models import Payment, Transaction
from ..tasks import refund_or_void_inactive_payment, release_unfinished_payments_task
from ..utils import (
    ALLOWED_GATEWAY_KINDS,
    clean_authorize,
    clean_capture,
    create_payment,
    create_payment_information,
    create_transaction,
    get_unfinished_payments,
    is_currency_supported,
    update_payment,
    validate_gateway_response,
)

NOT_ACTIVE_PAYMENT_ERROR = "This payment is no longer active."
EXAMPLE_ERROR = "Example dummy error"


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
    lines = fetch_checkout_lines(checkout_with_item)
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
    lines = fetch_checkout_lines(checkout_with_item)
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
    lines = fetch_checkout_lines(checkout_with_item)
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


@pytest.mark.parametrize(
    "func",
    [gateway.authorize, gateway.capture, gateway.confirm],
)
def test_payment_needs_to_be_active_for_any_charging_action(func, payment_dummy):
    payment_dummy.is_active = False
    with pytest.raises(PaymentError) as exc:
        func(payment_dummy, "token")
    assert exc.value.message == NOT_ACTIVE_PAYMENT_ERROR


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
    assert payment.charge_status == ChargeStatus.AUTHORIZED
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

    payment.charge_status = ChargeStatus.AUTHORIZED
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

    payment_dummy.charge_status = ChargeStatus.AUTHORIZED
    assert not payment_dummy.can_authorize()

    payment_dummy.charge_status = ChargeStatus.PARTIALLY_CHARGED
    assert not payment_dummy.can_authorize()

    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    assert not payment_dummy.can_authorize()


def test_can_capture(payment_txn_preauth: Payment):
    assert payment_txn_preauth.charge_status == ChargeStatus.AUTHORIZED

    payment_txn_preauth.is_active = False
    assert not payment_txn_preauth.can_capture()

    payment_txn_preauth.is_active = True
    assert payment_txn_preauth.can_capture()

    payment_txn_preauth.charge_status = ChargeStatus.NOT_CHARGED
    assert not payment_txn_preauth.can_capture()

    payment_txn_preauth.charge_status = ChargeStatus.PARTIALLY_CHARGED
    assert not payment_txn_preauth.can_capture()

    payment_txn_preauth.charge_status = ChargeStatus.FULLY_CHARGED
    assert not payment_txn_preauth.can_capture()

    payment_txn_preauth.captured_amount = 0
    payment_txn_preauth.transactions.all().delete()
    assert not payment_txn_preauth.can_capture()


def test_can_void(payment_txn_preauth: Payment):
    assert payment_txn_preauth.charge_status == ChargeStatus.AUTHORIZED

    payment_txn_preauth.is_active = False
    assert payment_txn_preauth.can_void()

    payment_txn_preauth.is_active = True
    assert payment_txn_preauth.can_void()

    payment_txn_preauth.charge_status = ChargeStatus.NOT_CHARGED
    assert not payment_txn_preauth.can_void()

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

    payment_dummy.charge_status = ChargeStatus.AUTHORIZED
    assert not payment_dummy.can_refund()

    payment_dummy.charge_status = ChargeStatus.PARTIALLY_CHARGED
    assert payment_dummy.can_refund()

    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    assert payment_dummy.can_refund()


def test_payment_get_total_authorized_empty_list():
    currency = "EUR"
    total = get_total_authorized([], currency)
    assert total.amount == Decimal("0.000")
    assert total.currency == currency


def test_payment_get_total_authorized(payment_kwargs):
    # given
    a = Decimal("101.01")
    b = Decimal("99.99")
    payment_kwargs["total"] = a
    p0 = Payment.objects.create(**payment_kwargs)
    payment_kwargs["charge_status"] = ChargeStatus.AUTHORIZED
    p1 = Payment.objects.create(**payment_kwargs)
    payment_kwargs["total"] = b
    p2 = Payment.objects.create(**payment_kwargs)
    payment_kwargs["is_active"] = False
    p3 = Payment.objects.create(**payment_kwargs)

    currency = "EUR"
    total = get_total_authorized([p0, p1, p2, p3], currency)
    assert total.amount == a + b
    assert total.currency == currency


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


@pytest.mark.parametrize(
    "partial, complete_order, result",
    [
        (True, True, True),
        (False, True, True),
        (False, False, True),
        (True, False, False),
    ],
)
def test_can_create_order(payment_txn_captured, partial, complete_order, result):
    payment_txn_captured.partial = partial
    payment_txn_captured.complete_order = complete_order
    payment_txn_captured.save()

    assert payment_txn_captured.can_create_order() == result


@freeze_time("2021-06-01 12:00:00")
@override_settings(UNFINISHED_PAYMENT_TTL=timedelta(days=1))
@pytest.mark.parametrize(
    "dates, order_exist, is_active, not_valid_kind, success, action_required",
    [
        (
            ["2021-06-01 12:00:00.0+00:00"],
            False,
            True,
            False,
            True,
            False,
        ),  # not release, date is to young
        (
            ["2021-05-01 12:00:00.0+00:00"],
            False,
            False,
            False,
            True,
            False,
        ),  # not release, inactive
        (
            ["2021-05-01 12:00:00.0+00:00", "2021-06-01 12:00:00.0+00:00"],
            False,
            True,
            False,
            True,
            False,
        ),  # not release, the second transaction is to young
        (
            ["2021-06-01 12:00:00.0+00:00", "2021-05-01 12:00:00.0+00:00"],
            False,
            True,
            False,
            True,
            False,
        ),  # not release, the first transaction is to young
        (
            ["2021-05-01 12:00:00.0+00:00"],
            True,
            True,
            False,
            True,
            False,
        ),  # not release, order exists
        (
            ["2021-05-01 12:00:00.0+00:00"],
            False,
            True,
            True,
            True,
            False,
        ),  # not release, not valid kind
        (
            ["2021-05-01 12:00:00.0+00:00"],
            False,
            True,
            False,
            False,
            False,
        ),  # not release, not success
        (
            ["2021-05-01 12:00:00.0+00:00"],
            False,
            True,
            False,
            True,
            True,
        ),  # not release, action required
    ],
)
def test_get_unfinished_payments_with_payments_not_to_release(
    payment_dummy,
    dates,
    order_exist,
    is_active,
    not_valid_kind,
    success,
    action_required,
):
    payment = payment_dummy
    if not order_exist:
        payment.order = None
        payment.save()

    if not is_active:
        payment.is_active = False
        payment.save()

    for date in dates:
        with freeze_time(date):
            kind = (
                TransactionKind.CAPTURE
                if not not_valid_kind
                else TransactionKind.CANCEL
            )
            Transaction.objects.create(
                payment=payment,
                amount=payment.total,
                kind=kind,
                gateway_response={},
                is_success=success,
                action_required=action_required,
            )

    payments = get_unfinished_payments()
    assert payments.count() == 0


@mock.patch("saleor.payment.tasks.get_unfinished_payments")
@mock.patch("saleor.payment.tasks.refund_or_void_inactive_payment")
def test_release_unfinished_payments_task(
    release, get_unfinished_payments, payment_dummy
):
    # given
    qs = Mock()
    get_unfinished_payments.return_value = qs
    qs.iterator.return_value = iter([payment_dummy])
    # when
    release_unfinished_payments_task()
    # then
    release.delay.assert_called_once_with(payment_dummy.pk)


@mock.patch("saleor.payment.gateway.payment_refund_or_void")
@mock.patch("saleor.payment.tasks.task_logger")
def test_refund_or_void_inactive_payment(
    task_logger, payment_refund_or_void, checkout_with_payments_factory
):
    # given
    payment = checkout_with_payments_factory().payments.get()
    # when
    refund_or_void_inactive_payment(payment.pk)
    # then
    payment_refund_or_void.assert_called_once_with(payment, ANY, ANY)
    task_logger.info.assert_called_once_with("Released payment %d.", payment.pk)


@mock.patch("saleor.payment.gateway.payment_refund_or_void")
@mock.patch("saleor.payment.tasks.task_logger")
def test_failed_refund_or_void_inactive_payment(
    task_logger, release_checkout_payment, checkout_with_payments_factory
):
    # given
    payment = checkout_with_payments_factory().payments.get()
    e = PaymentError("An error")
    release_checkout_payment.side_effect = e
    # when
    with pytest.raises(PaymentError):
        refund_or_void_inactive_payment(payment.pk)
    # then
    release_checkout_payment.assert_called_once_with(payment, ANY, ANY)
    task_logger.error.assert_called_once_with(
        "Release payment %d failed.", payment.pk, e
    )
