import datetime
import logging
from decimal import Decimal
from unittest.mock import patch

import pytest
from freezegun import freeze_time

from ...checkout import CheckoutAuthorizeStatus
from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...order import OrderAuthorizeStatus, OrderChargeStatus, OrderGrantedRefundStatus
from ...plugins.manager import get_plugins_manager
from .. import TransactionEventType
from ..interface import (
    PaymentLineData,
    PaymentLinesData,
    TransactionRequestEventResponse,
    TransactionRequestResponse,
)
from ..models import TransactionEvent
from ..utils import (
    create_failed_transaction_event,
    create_manual_adjustment_events,
    create_payment_lines_information,
    create_transaction_event_for_transaction_session,
    create_transaction_event_from_request_and_webhook_response,
    deduplicate_event,
    get_channel_slug_from_payment,
    get_correct_event_types_based_on_request_type,
    get_transaction_event_amount,
    parse_transaction_action_data,
    recalculate_refundable_for_checkout,
    try_void_or_refund_inactive_payment,
)


def test_create_payment_lines_information_order(payment_dummy):
    # given
    manager = get_plugins_manager(allow_replica=False)

    # when
    payment_lines_data = create_payment_lines_information(payment_dummy, manager)

    # then
    order = payment_dummy.order
    assert payment_lines_data.lines == [
        PaymentLineData(
            amount=line.unit_price_gross_amount,
            variant_id=line.variant_id,
            product_name=f"{line.product_name}, {line.variant_name}",
            product_sku=line.product_sku,
            quantity=line.quantity,
        )
        for line in order.lines.all()
    ]
    assert payment_lines_data.shipping_amount == order.shipping_price_gross_amount
    assert payment_lines_data.voucher_amount == Decimal("0.00")


def test_create_payment_lines_information_order_with_voucher(payment_dummy):
    # given
    voucher_amount = Decimal("12.30")
    order = payment_dummy.order
    order.undiscounted_total_gross_amount += voucher_amount
    manager = get_plugins_manager(allow_replica=False)

    # when
    payment_lines_data = create_payment_lines_information(payment_dummy, manager)

    # then
    assert payment_lines_data.lines == [
        PaymentLineData(
            amount=line.unit_price_gross_amount,
            variant_id=line.variant_id,
            product_name=f"{line.product_name}, {line.variant_name}",
            product_sku=line.product_sku,
            quantity=line.quantity,
        )
        for line in order.lines.all()
    ]
    assert payment_lines_data.shipping_amount == order.shipping_price_gross_amount
    assert payment_lines_data.voucher_amount == -voucher_amount


def get_expected_checkout_payment_lines(manager, checkout_info, lines, address):
    expected_payment_lines = []

    for line_info in lines:
        unit_gross = manager.calculate_checkout_line_unit_price(
            checkout_info,
            lines,
            line_info,
            address,
        ).gross.amount
        quantity = line_info.line.quantity
        variant_id = line_info.variant.id
        product_name = f"{line_info.variant.product.name}, {line_info.variant.name}"
        product_sku = line_info.variant.sku
        expected_payment_lines.append(
            PaymentLineData(
                amount=unit_gross,
                variant_id=variant_id,
                product_name=product_name,
                product_sku=product_sku,
                quantity=quantity,
            )
        )

    shipping_gross = manager.calculate_checkout_shipping(
        checkout_info=checkout_info,
        lines=lines,
        address=address,
    ).gross.amount

    return PaymentLinesData(
        lines=expected_payment_lines,
        shipping_amount=shipping_gross,
        voucher_amount=Decimal("0.00"),
    )


def test_create_payment_lines_information_checkout(payment_dummy, checkout_with_items):
    # given
    manager = get_plugins_manager(allow_replica=False)
    payment_dummy.order = None
    payment_dummy.checkout = checkout_with_items

    # when
    payment_lines = create_payment_lines_information(payment_dummy, manager)

    # then
    lines, _ = fetch_checkout_lines(checkout_with_items)
    checkout_info = fetch_checkout_info(checkout_with_items, lines, manager)
    address = checkout_with_items.shipping_address
    expected_payment_lines = get_expected_checkout_payment_lines(
        manager, checkout_info, lines, address
    )

    assert payment_lines == expected_payment_lines


def test_create_payment_lines_information_checkout_with_voucher(
    payment_dummy, checkout_with_items
):
    # given
    manager = get_plugins_manager(allow_replica=False)
    voucher_amount = Decimal("12.30")
    payment_dummy.order = None
    checkout_with_items.discount_amount = voucher_amount
    payment_dummy.checkout = checkout_with_items

    # when
    payment_lines = create_payment_lines_information(payment_dummy, manager)

    # then
    lines, _ = fetch_checkout_lines(checkout_with_items)
    checkout_info = fetch_checkout_info(checkout_with_items, lines, manager)
    address = checkout_with_items.shipping_address
    expected_payment_lines_data = get_expected_checkout_payment_lines(
        manager, checkout_info, lines, address
    )

    expected_payment_lines_data.voucher_amount = -voucher_amount

    assert payment_lines == expected_payment_lines_data


def test_create_payment_lines_information_invalid_payment(payment_dummy):
    # given
    manager = get_plugins_manager(allow_replica=False)
    payment_dummy.order = None

    # when
    payment_lines_data = create_payment_lines_information(payment_dummy, manager)

    # then
    assert not payment_lines_data.lines
    assert not payment_lines_data.shipping_amount
    assert not payment_lines_data.voucher_amount


def test_get_channel_slug_from_payment_with_order(payment_dummy):
    expected = payment_dummy.order.channel.slug
    assert get_channel_slug_from_payment(payment_dummy) == expected


def test_get_channel_slug_from_payment_with_checkout(checkout_with_payments):
    payment = checkout_with_payments.payments.first()
    expected = checkout_with_payments.channel.slug
    assert get_channel_slug_from_payment(payment) == expected


def test_get_channel_slug_from_payment_without_order(
    checkout_with_payments,
):
    payment = checkout_with_payments.payments.first()
    payment.checkout.delete()
    payment.refresh_from_db()
    assert not get_channel_slug_from_payment(payment)


@patch("saleor.payment.utils.update_payment_charge_status")
@patch("saleor.payment.utils.get_channel_slug_from_payment")
@patch("saleor.payment.gateway.payment_refund_or_void")
def test_try_void_or_refund_inactive_payment_failed_transaction(
    refund_or_void_mock,
    get_channel_slug_from_payment_mock,
    update_payment_charge_status_mock,
    payment_txn_capture_failed,
):
    transaction = payment_txn_capture_failed.transactions.first()

    assert not try_void_or_refund_inactive_payment(
        payment_txn_capture_failed, transaction, None
    )
    assert not update_payment_charge_status_mock.called
    assert not get_channel_slug_from_payment_mock.called
    assert not refund_or_void_mock.called


@patch("saleor.payment.utils.get_channel_slug_from_payment")
@patch("saleor.payment.gateway.payment_refund_or_void")
def test_try_void_or_refund_inactive_payment_transaction_success(
    refund_or_void_mock,
    get_channel_slug_from_payment_mock,
    payment_txn_captured,
):
    transaction = payment_txn_captured.transactions.first()

    assert not try_void_or_refund_inactive_payment(
        payment_txn_captured, transaction, None
    )
    assert get_channel_slug_from_payment_mock.called
    assert refund_or_void_mock.called


def test_parse_transaction_action_data_with_only_psp_reference():
    # given
    expected_psp_reference = "psp:122:222"
    response_data = {"pspReference": expected_psp_reference}

    # when
    parsed_data, _ = parse_transaction_action_data(
        response_data, TransactionEventType.AUTHORIZATION_REQUEST
    )

    # then
    assert isinstance(parsed_data, TransactionRequestResponse)

    assert parsed_data.psp_reference == expected_psp_reference
    assert parsed_data.event is None


@pytest.mark.parametrize(
    ("event_time", "expected_datetime"),
    [
        (
            "2023-10-17T10:18:28.111Z",
            datetime.datetime(2023, 10, 17, 10, 18, 28, 111000, tzinfo=datetime.UTC),
        ),
        ("2011-11-04", datetime.datetime(2011, 11, 4, 0, 0, tzinfo=datetime.UTC)),
        (
            "2011-11-04T00:05:23",
            datetime.datetime(2011, 11, 4, 0, 5, 23, tzinfo=datetime.UTC),
        ),
        (
            "2011-11-04T00:05:23Z",
            datetime.datetime(2011, 11, 4, 0, 5, 23, tzinfo=datetime.UTC),
        ),
        (
            "20111104T000523",
            datetime.datetime(2011, 11, 4, 0, 5, 23, tzinfo=datetime.UTC),
        ),
        (
            "2011-W01-2T00:05:23.283",
            datetime.datetime(2011, 1, 4, 0, 5, 23, 283000, tzinfo=datetime.UTC),
        ),
        (
            "2011-11-04 00:05:23.283",
            datetime.datetime(2011, 11, 4, 0, 5, 23, 283000, tzinfo=datetime.UTC),
        ),
        (
            "2011-11-04 00:05:23.283+00:00",
            datetime.datetime(2011, 11, 4, 0, 5, 23, 283000, tzinfo=datetime.UTC),
        ),
        (
            "1994-11-05T13:15:30Z",
            datetime.datetime(1994, 11, 5, 13, 15, 30, tzinfo=datetime.UTC),
        ),
    ],
)
def test_parse_transaction_action_data_with_provided_time(
    event_time, expected_datetime
):
    # given
    expected_psp_reference = "psp:122:222"
    event_amount = 12.00
    event_type = TransactionEventType.CHARGE_SUCCESS
    event_url = "http://localhost:3000/event/ref123"
    event_cause = "No cause"

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
        "time": event_time,
        "externalUrl": event_url,
        "message": event_cause,
    }

    # when
    parsed_data, error_msg = parse_transaction_action_data(
        response_data, TransactionEventType.CHARGE_REQUEST
    )
    # then
    assert parsed_data.event.time == expected_datetime


def test_parse_transaction_action_data_with_event_all_fields_provided():
    # given
    expected_psp_reference = "psp:122:222"
    event_amount = 12.00
    event_type = TransactionEventType.CHARGE_SUCCESS
    event_time = "2022-11-18T13:25:58.169685+00:00"
    event_url = "http://localhost:3000/event/ref123"
    event_cause = "No cause"

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
        "time": event_time,
        "externalUrl": event_url,
        "message": event_cause,
    }

    # when
    parsed_data, error_msg = parse_transaction_action_data(
        response_data, TransactionEventType.CHARGE_REQUEST
    )
    # then
    assert isinstance(parsed_data, TransactionRequestResponse)
    assert error_msg is None

    assert parsed_data.psp_reference == expected_psp_reference
    assert isinstance(parsed_data.event, TransactionRequestEventResponse)
    assert parsed_data.event.psp_reference == expected_psp_reference
    assert parsed_data.event.amount == event_amount
    assert parsed_data.event.time == datetime.datetime.fromisoformat(event_time)
    assert parsed_data.event.external_url == event_url
    assert parsed_data.event.message == event_cause
    assert parsed_data.event.type == event_type


def test_parse_transaction_action_data_with_incorrect_result():
    # given
    expected_psp_reference = "psp:122:222"
    event_amount = 12.00
    event_type = TransactionEventType.CHARGE_SUCCESS
    event_time = "2022-11-18T13:25:58.169685+00:00"
    event_url = "http://localhost:3000/event/ref123"
    event_cause = "No cause"

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
        "time": event_time,
        "externalUrl": event_url,
        "message": event_cause,
    }

    # when
    parsed_data, error_msg = parse_transaction_action_data(
        response_data, TransactionEventType.REFUND_REQUEST
    )

    # then
    assert parsed_data is None
    assert isinstance(error_msg, str)


@freeze_time("2018-05-31 12:00:01")
def test_parse_transaction_action_data_with_event_only_mandatory_fields():
    # given
    expected_psp_reference = "psp:122:222"
    expected_amount = Decimal("10.00")
    response_data = {
        "pspReference": expected_psp_reference,
        "result": TransactionEventType.CHARGE_SUCCESS.upper(),
        "amount": expected_amount,
    }

    # when
    parsed_data, _ = parse_transaction_action_data(
        response_data, TransactionEventType.CHARGE_REQUEST
    )

    # then
    assert isinstance(parsed_data, TransactionRequestResponse)

    assert parsed_data.psp_reference == expected_psp_reference
    assert isinstance(parsed_data.event, TransactionRequestEventResponse)
    assert parsed_data.event.psp_reference == expected_psp_reference
    assert parsed_data.event.type == TransactionEventType.CHARGE_SUCCESS
    assert parsed_data.event.amount == expected_amount
    assert parsed_data.event.time == datetime.datetime.now(tz=datetime.UTC)
    assert parsed_data.event.external_url == ""
    assert parsed_data.event.message == ""


@freeze_time("2018-05-31 12:00:01")
def test_parse_transaction_action_data_with_missing_psp_reference():
    # given
    response_data = {}

    # when
    parsed_data, _ = parse_transaction_action_data(
        response_data, TransactionEventType.AUTHORIZATION_REQUEST
    )

    # then
    assert parsed_data is None


def test_parse_transaction_action_data_with_missing_optional_psp_reference():
    # given
    response_data = {}

    # when
    parsed_data, _ = parse_transaction_action_data(
        response_data,
        TransactionEventType.AUTHORIZATION_ACTION_REQUIRED,
    )

    # then
    assert parsed_data


def test_parse_transaction_action_data_with_missing_mandatory_event_fields():
    # given
    expected_psp_reference = "psp:122:222"

    response_data = {"pspReference": expected_psp_reference, "amount": Decimal("1")}

    # when
    parsed_data, _ = parse_transaction_action_data(
        response_data, TransactionEventType.AUTHORIZATION_REQUEST
    )

    # then
    assert parsed_data is None


def test_create_failed_transaction_event(transaction_item_generator):
    # given
    transaction = transaction_item_generator()
    cause = "Test failure"
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction.id,
    )

    # when
    failed_event = create_failed_transaction_event(request_event, cause=cause)

    # then
    assert failed_event.type == TransactionEventType.CHARGE_FAILURE
    assert failed_event.amount_value == request_event.amount_value
    assert failed_event.currency == request_event.currency
    assert failed_event.transaction_id == transaction.id


def test_create_transaction_event_from_request_and_webhook_response_with_psp_reference(
    transaction_item_generator,
    app,
):
    # given
    transaction = transaction_item_generator()
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction.id,
    )
    expected_psp_reference = "psp:122:222"
    response_data = {"pspReference": expected_psp_reference}

    # when
    create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    request_event.refresh_from_db()
    assert request_event.psp_reference == expected_psp_reference
    assert TransactionEvent.objects.count() == 1


@pytest.mark.parametrize(
    ("event_type", "result_event_type"),
    [
        (
            TransactionEventType.REFUND_REQUEST,
            TransactionEventType.REFUND_FAILURE,
        ),
        (
            TransactionEventType.CHARGE_REQUEST,
            TransactionEventType.CHARGE_FAILURE,
        ),
        (
            TransactionEventType.CANCEL_REQUEST,
            TransactionEventType.CANCEL_FAILURE,
        ),
    ],
)
def test_create_transaction_event_from_request_and_webhook_response_with_no_psp_reference_valid_event(
    event_type, result_event_type, transaction_item_generator, app
):
    # given
    transaction = transaction_item_generator()
    event_amount = Decimal(11.00)
    request_event = TransactionEvent.objects.create(
        type=event_type,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction.id,
    )
    event_count = transaction.events.count()
    response_data = {
        "amount": event_amount,
        "result": result_event_type.upper(),
    }

    # when
    event = create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    request_event.refresh_from_db()
    transaction.refresh_from_db()
    assert request_event.psp_reference is None
    assert transaction.events.count() == event_count + 1
    assert event.psp_reference is None
    assert event.type == result_event_type
    assert not event.message


@pytest.mark.parametrize(
    ("event_type", "result_event_type"),
    [
        (
            TransactionEventType.REFUND_REQUEST,
            TransactionEventType.REFUND_SUCCESS,
        ),
        (
            TransactionEventType.CHARGE_REQUEST,
            TransactionEventType.CHARGE_SUCCESS,
        ),
        (
            TransactionEventType.CANCEL_REQUEST,
            TransactionEventType.CANCEL_SUCCESS,
        ),
        (
            TransactionEventType.AUTHORIZATION_REQUEST,
            TransactionEventType.AUTHORIZATION_SUCCESS,
        ),
    ],
)
def test_create_transaction_event_from_request_and_webhook_response_with_no_psp_reference_invalid_event(
    event_type,
    result_event_type,
    transaction_item_generator,
    app,
    caplog,
):
    # given
    transaction = transaction_item_generator()
    event_amount = Decimal(11.00)
    request_event = TransactionEvent.objects.create(
        type=event_type,
        amount_value=event_amount,
        currency="USD",
        transaction_id=transaction.id,
    )
    event_count = transaction.events.count()
    response_data = {
        "amount": event_amount,
        "result": result_event_type.upper(),
    }

    # when
    event = create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    request_event.refresh_from_db()
    transaction.refresh_from_db()
    assert request_event.psp_reference is None
    assert transaction.events.count() == event_count + 1
    assert event.psp_reference is None
    assert event.transaction_id == transaction.id
    error_msg = f"Providing `pspReference` is required for {result_event_type.upper()}."
    assert event.message == error_msg
    assert caplog.records[0].levelno == logging.WARNING
    assert caplog.records[0].message == error_msg


@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_from_request_and_webhook_response_part_event(
    transaction_item_generator,
    app,
):
    # given
    transaction = transaction_item_generator()
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction.id,
    )
    expected_psp_reference = "psp:122:222"
    amount = request_event.amount_value
    response_data = {
        "pspReference": expected_psp_reference,
        "result": TransactionEventType.CHARGE_SUCCESS.upper(),
        "amount": amount,
    }

    # when
    event = create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    assert TransactionEvent.objects.count() == 2
    request_event.refresh_from_db()
    assert request_event.psp_reference == expected_psp_reference
    assert event
    assert event.psp_reference == expected_psp_reference
    assert event.amount_value == amount
    assert event.created_at == datetime.datetime.now(tz=datetime.UTC)
    assert event.external_url == ""
    assert event.message == ""
    assert event.type == TransactionEventType.CHARGE_SUCCESS


@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_from_request_updates_order_charge(
    transaction_item_generator, app, order_with_lines
):
    # given
    order = order_with_lines
    transaction = transaction_item_generator(order_id=order.pk)
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction.id,
    )

    event_amount = 12.00
    event_type = TransactionEventType.CHARGE_SUCCESS

    expected_psp_reference = "psp:122:222"

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
    }

    # when
    create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    order.refresh_from_db()
    assert order.total_charged_amount == Decimal(event_amount)
    assert order.charge_status == OrderChargeStatus.PARTIAL
    assert order.search_vector


@patch("saleor.plugins.manager.PluginsManager.order_paid")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_from_request_triggers_webhooks_when_fully_paid(
    mock_order_fully_paid,
    mock_order_updated,
    mock_order_paid,
    transaction_item_generator,
    app,
    order_with_lines,
    django_capture_on_commit_callbacks,
):
    # given
    order = order_with_lines
    transaction = transaction_item_generator(order_id=order.pk)
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=order.total.gross.amount,
        currency="USD",
        transaction_id=transaction.id,
    )

    event_amount = order.total.gross.amount
    event_type = TransactionEventType.CHARGE_SUCCESS

    expected_psp_reference = "psp:122:222"

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
    }

    # when
    with django_capture_on_commit_callbacks(execute=True):
        create_transaction_event_from_request_and_webhook_response(
            request_event, app, response_data
        )

    # then
    order.refresh_from_db()
    assert order.charge_status == OrderChargeStatus.FULL
    mock_order_fully_paid.assert_called_once_with(order, webhooks=set())
    mock_order_updated.assert_called_once_with(order, webhooks=set())
    mock_order_paid.assert_called_once_with(order, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_paid")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_from_request_triggers_webhooks_when_partially_paid(
    mock_order_fully_paid,
    mock_order_updated,
    mock_order_paid,
    transaction_item_generator,
    app,
    order_with_lines,
    django_capture_on_commit_callbacks,
):
    # given
    order = order_with_lines
    transaction = transaction_item_generator(order_id=order.pk)
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=Decimal("12.00"),
        currency="USD",
        transaction_id=transaction.id,
    )

    event_amount = Decimal("12.00")
    event_type = TransactionEventType.CHARGE_SUCCESS

    expected_psp_reference = "psp:122:222"

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
    }

    # when
    with django_capture_on_commit_callbacks(execute=True):
        create_transaction_event_from_request_and_webhook_response(
            request_event, app, response_data
        )

    # then
    order.refresh_from_db()
    assert order_with_lines.charge_status == OrderChargeStatus.PARTIAL
    assert not mock_order_fully_paid.called
    mock_order_updated.assert_called_once_with(order_with_lines, webhooks=set())
    mock_order_paid.assert_called_once_with(order, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_from_request_triggers_webhooks_when_fully_refunded(
    mock_order_fully_refunded,
    mock_order_updated,
    mock_order_refunded,
    transaction_item_generator,
    app,
    order_with_lines,
    django_capture_on_commit_callbacks,
):
    # given
    order = order_with_lines
    transaction = transaction_item_generator(order_id=order.pk)
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=order.total.gross.amount,
        currency="USD",
        transaction_id=transaction.id,
    )

    event_amount = order.total.gross.amount
    event_type = TransactionEventType.REFUND_SUCCESS

    expected_psp_reference = "psp:122:222"

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
    }

    # when
    with django_capture_on_commit_callbacks(execute=True):
        create_transaction_event_from_request_and_webhook_response(
            request_event, app, response_data
        )

    # then
    order.refresh_from_db()

    mock_order_fully_refunded.assert_called_once_with(order, webhooks=set())
    mock_order_updated.assert_called_once_with(order, webhooks=set())
    mock_order_refunded.assert_called_once_with(order, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_from_request_triggers_webhooks_partially_refunded(
    mock_order_fully_refunded,
    mock_order_updated,
    mock_order_refunded,
    transaction_item_generator,
    app,
    order_with_lines,
    django_capture_on_commit_callbacks,
):
    # given
    order = order_with_lines
    transaction = transaction_item_generator(order_id=order.pk)
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=Decimal("12.00"),
        currency="USD",
        transaction_id=transaction.id,
    )

    event_amount = Decimal("12.00")
    event_type = TransactionEventType.REFUND_SUCCESS

    expected_psp_reference = "psp:122:222"

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
    }

    # when
    with django_capture_on_commit_callbacks(execute=True):
        create_transaction_event_from_request_and_webhook_response(
            request_event, app, response_data
        )

    # then
    order.refresh_from_db()

    assert not mock_order_fully_refunded.called
    mock_order_updated.assert_called_once_with(order_with_lines, webhooks=set())
    mock_order_refunded.assert_called_once_with(order, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_from_request_triggers_webhooks_when_authorized(
    mock_order_fully_paid,
    mock_order_updated,
    transaction_item_generator,
    app,
    order_with_lines,
    django_capture_on_commit_callbacks,
):
    # given
    order = order_with_lines
    transaction = transaction_item_generator(order_id=order.pk)
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.AUTHORIZATION_REQUEST,
        amount_value=order.total.gross.amount,
        currency="USD",
        transaction_id=transaction.id,
    )

    event_amount = order.total.gross.amount
    event_type = TransactionEventType.AUTHORIZATION_SUCCESS

    expected_psp_reference = "psp:122:222"

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
    }

    # when
    with django_capture_on_commit_callbacks(execute=True):
        create_transaction_event_from_request_and_webhook_response(
            request_event, app, response_data
        )

    # then
    order.refresh_from_db()
    assert order_with_lines.authorize_status == OrderAuthorizeStatus.FULL
    assert not mock_order_fully_paid.called
    mock_order_updated.assert_called_once_with(order_with_lines, webhooks=set())


@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_from_request_updates_order_authorize(
    transaction_item_generator, app, order_with_lines
):
    # given
    order = order_with_lines
    transaction = transaction_item_generator(order_id=order.pk)
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.AUTHORIZATION_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction.id,
    )

    event_amount = 12.00
    event_type = TransactionEventType.AUTHORIZATION_SUCCESS

    expected_psp_reference = "psp:122:222"

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
    }

    # when
    create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    order.refresh_from_db()
    assert order.total_authorized_amount == Decimal(event_amount)
    assert order.authorize_status == OrderAuthorizeStatus.PARTIAL


@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_from_request_and_webhook_response_full_event(
    transaction_item_generator,
    app,
):
    # given
    transaction = transaction_item_generator()
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction.id,
    )

    event_amount = 12.00
    event_type = TransactionEventType.CHARGE_FAILURE
    event_time = "2022-11-18T13:25:58.169685+00:00"
    event_url = "http://localhost:3000/event/ref123"
    event_cause = "No cause"

    expected_psp_reference = "psp:122:222"

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
        "time": event_time,
        "externalUrl": event_url,
        "message": event_cause,
        "actions": ["CHARGE", "CHARGE", "CANCEL"],
    }

    # when
    event = create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    transaction.refresh_from_db()
    assert len(transaction.available_actions) == 2
    assert set(transaction.available_actions) == {"charge", "cancel"}
    assert transaction.events.count() == 2
    request_event.refresh_from_db()
    assert request_event.psp_reference == expected_psp_reference
    assert event
    assert event.psp_reference == expected_psp_reference
    assert event.amount_value == event_amount
    assert event.created_at == datetime.datetime.fromisoformat(event_time)
    assert event.external_url == event_url
    assert event.message == event_cause
    assert event.type == event_type


@patch("saleor.checkout.tasks.automatic_checkout_completion_task.delay")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_create_transaction_event_from_request_when_paid(
    mocked_checkout_fully_paid,
    mocked_automatic_checkout_completion_task,
    transaction_item_generator,
    app,
    checkout_with_prices,
    django_capture_on_commit_callbacks,
):
    # given
    checkout = checkout_with_prices

    transaction = transaction_item_generator(checkout_id=checkout.pk)
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=checkout.total.gross.amount,
        currency="USD",
        transaction_id=transaction.id,
    )

    event_amount = checkout.total.gross.amount
    event_type = TransactionEventType.CHARGE_SUCCESS

    expected_psp_reference = "psp:122:222"

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
    }

    # when
    with django_capture_on_commit_callbacks(execute=True):
        create_transaction_event_from_request_and_webhook_response(
            request_event, app, response_data
        )

    # then
    checkout.refresh_from_db()
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    mocked_checkout_fully_paid.assert_called_once_with(checkout, webhooks=set())
    mocked_automatic_checkout_completion_task.assert_not_called()


@patch("saleor.checkout.tasks.automatic_checkout_completion_task.delay")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_create_transaction_event_from_request_when_authorized(
    mocked_checkout_fully_paid,
    mocked_automatic_checkout_completion_task,
    transaction_item_generator,
    app,
    checkout_with_prices,
    django_capture_on_commit_callbacks,
):
    # given
    checkout = checkout_with_prices

    channel = checkout.channel
    assert channel.automatically_complete_fully_paid_checkouts is False

    transaction = transaction_item_generator(checkout_id=checkout.pk)
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.AUTHORIZATION_REQUEST,
        amount_value=checkout.total.gross.amount,
        currency="USD",
        transaction_id=transaction.id,
    )

    event_amount = checkout.total.gross.amount
    event_type = TransactionEventType.AUTHORIZATION_SUCCESS

    expected_psp_reference = "psp:122:222"

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
    }

    # when
    with django_capture_on_commit_callbacks(execute=True):
        create_transaction_event_from_request_and_webhook_response(
            request_event, app, response_data
        )

    # then
    checkout.refresh_from_db()
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    mocked_checkout_fully_paid.assert_not_called()
    mocked_automatic_checkout_completion_task.assert_not_called()


@patch("saleor.checkout.tasks.automatic_checkout_completion_task.delay")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_create_transaction_event_from_request_when_paid_triggers_checkout_completion(
    mocked_checkout_fully_paid,
    mocked_automatic_checkout_completion_task,
    transaction_item_generator,
    app,
    checkout_with_prices,
    plugins_manager,
    django_capture_on_commit_callbacks,
):
    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)

    channel = checkout_info.channel
    channel.automatically_complete_fully_paid_checkouts = True
    channel.save(update_fields=["automatically_complete_fully_paid_checkouts"])

    transaction = transaction_item_generator(checkout_id=checkout.pk)
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=checkout.total.gross.amount,
        currency="USD",
        transaction_id=transaction.id,
    )

    event_amount = checkout.total.gross.amount
    event_type = TransactionEventType.CHARGE_SUCCESS

    expected_psp_reference = "psp:122:222"

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
    }

    # when
    with django_capture_on_commit_callbacks(execute=True):
        create_transaction_event_from_request_and_webhook_response(
            request_event, app, response_data
        )

    # then
    checkout.refresh_from_db()
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    mocked_checkout_fully_paid.assert_called_once_with(checkout, webhooks=set())
    mocked_automatic_checkout_completion_task.assert_called_once_with(
        checkout.pk, None, app.id
    )


@patch("saleor.checkout.tasks.automatic_checkout_completion_task.delay")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_create_transaction_event_from_request_when_authorized_triggers_checkout_completion(
    mocked_checkout_fully_paid,
    mocked_automatic_checkout_completion_task,
    transaction_item_generator,
    app,
    checkout_with_prices,
    plugins_manager,
    django_capture_on_commit_callbacks,
):
    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)

    channel = checkout_info.channel
    channel.automatically_complete_fully_paid_checkouts = True
    channel.save(update_fields=["automatically_complete_fully_paid_checkouts"])

    transaction = transaction_item_generator(checkout_id=checkout.pk)
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.AUTHORIZATION_REQUEST,
        amount_value=checkout.total.gross.amount,
        currency="USD",
        transaction_id=transaction.id,
    )

    event_amount = checkout.total.gross.amount
    event_type = TransactionEventType.AUTHORIZATION_SUCCESS

    expected_psp_reference = "psp:122:222"

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
    }

    # when
    with django_capture_on_commit_callbacks(execute=True):
        create_transaction_event_from_request_and_webhook_response(
            request_event, app, response_data
        )

    # then
    checkout.refresh_from_db()
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    mocked_checkout_fully_paid.assert_not_called()
    mocked_automatic_checkout_completion_task.assert_called_once_with(
        checkout.pk, None, app.id
    )


def test_create_transaction_event_from_request_and_webhook_response_incorrect_data(
    transaction_item_generator,
    app,
):
    # given
    transaction = transaction_item_generator()
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction.id,
    )
    response_data = {"wrong-data": "psp:122:222"}

    # when
    failed_event = create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    request_event.refresh_from_db()
    assert TransactionEvent.objects.count() == 2

    assert failed_event
    assert failed_event.type == TransactionEventType.CHARGE_FAILURE
    assert failed_event.amount_value == request_event.amount_value
    assert failed_event.currency == request_event.currency
    assert failed_event.transaction_id == transaction.id


@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_from_request_and_webhook_response_twice_auth(
    transaction_item_generator,
    app,
):
    # given
    transaction = transaction_item_generator()
    transaction.events.create(
        type=TransactionEventType.AUTHORIZATION_SUCCESS,
        amount_value=Decimal(22.00),
        currency="USD",
    )

    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.AUTHORIZATION_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction.id,
    )

    event_amount = 12.00
    event_type = TransactionEventType.AUTHORIZATION_SUCCESS
    event_time = "2022-11-18T13:25:58.169685+00:00"
    event_url = "http://localhost:3000/event/ref123"

    expected_psp_reference = "psp:122:222"

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
        "time": event_time,
        "externalUrl": event_url,
    }

    # when
    failed_event = create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    assert TransactionEvent.objects.count() == 3
    request_event.refresh_from_db()
    assert request_event.psp_reference == expected_psp_reference
    assert failed_event
    assert failed_event.psp_reference == expected_psp_reference
    assert failed_event.type == TransactionEventType.AUTHORIZATION_FAILURE


@pytest.mark.parametrize(
    ("first_event_amount", "second_event_amount"),
    [(12.02, 12.02), ("12.02", 12.02), (12.02, "12.02"), ("12.02", "12.02")],
)
@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_from_request_and_webhook_response_same_event(
    transaction_item_generator,
    first_event_amount,
    second_event_amount,
    app,
):
    # given
    expected_psp_reference = "psp:122:222"
    event_amount = first_event_amount
    event_type = TransactionEventType.AUTHORIZATION_SUCCESS
    event_time = "2022-11-18T13:25:58.169685+00:00"
    event_url = "http://localhost:3000/event/ref123"

    transaction = transaction_item_generator()
    existing_authorize_success = transaction.events.create(
        type=event_type,
        amount_value=event_amount,
        currency="USD",
        psp_reference=expected_psp_reference,
    )

    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.AUTHORIZATION_REQUEST,
        amount_value=second_event_amount,
        currency="USD",
        transaction_id=transaction.id,
    )

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": second_event_amount,
        "result": event_type.upper(),
        "time": event_time,
        "externalUrl": event_url,
    }

    # when
    event = create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    assert TransactionEvent.objects.count() == 2
    request_event.refresh_from_db()
    assert request_event.psp_reference == expected_psp_reference
    assert event
    assert event.pk == existing_authorize_success.pk


@pytest.mark.parametrize(
    "event_amount",
    [None, "NaN", "-Inf", "Inf", "One"],
)
@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_from_request_handle_incorrect_values(
    transaction_item_generator,
    event_amount,
    app,
):
    # given
    expected_psp_reference = "psp:122:222"
    event_amount = event_amount
    event_type = TransactionEventType.AUTHORIZATION_SUCCESS
    event_time = "2022-11-18T13:25:58.169685+00:00"
    event_url = "http://localhost:3000/event/ref123"

    transaction = transaction_item_generator()

    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.AUTHORIZATION_REQUEST,
        amount_value=Decimal(10),
        currency="USD",
        transaction_id=transaction.id,
        psp_reference=expected_psp_reference,
    )

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
        "time": event_time,
        "externalUrl": event_url,
    }

    # when
    event = create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    assert event.type == TransactionEventType.AUTHORIZATION_FAILURE
    assert TransactionEvent.objects.count() == 2
    request_event.refresh_from_db()
    assert request_event.psp_reference == expected_psp_reference


@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_from_request_and_webhook_response_different_amount(
    transaction_item_generator,
    app,
):
    # given
    expected_psp_reference = "psp:122:222"
    authorize_event_amount = Decimal(12.00)
    event_type = TransactionEventType.AUTHORIZATION_SUCCESS
    event_time = "2022-11-18T13:25:58.169685+00:00"
    event_url = "http://localhost:3000/event/ref123"

    transaction = transaction_item_generator()
    transaction.events.create(
        type=event_type,
        amount_value=authorize_event_amount,
        currency="USD",
        psp_reference=expected_psp_reference,
    )

    second_authorize_event_amount = Decimal(33.00)
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.AUTHORIZATION_REQUEST,
        amount_value=second_authorize_event_amount,
        currency="USD",
        transaction_id=transaction.id,
    )

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": second_authorize_event_amount,
        "result": event_type.upper(),
        "time": event_time,
        "externalUrl": event_url,
    }

    # when
    failed_event = create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    assert TransactionEvent.objects.count() == 3
    request_event.refresh_from_db()
    assert request_event.psp_reference == expected_psp_reference
    assert failed_event
    assert failed_event.psp_reference == expected_psp_reference
    assert failed_event.type == TransactionEventType.AUTHORIZATION_FAILURE


@freeze_time("2018-05-31 12:00:01")
def test_create_event_from_request_and_webhook_missing_response_calculate_refundable(
    transaction_item_generator,
    checkout,
    app,
):
    # given
    checkout.automatically_refundable = True
    checkout.save()

    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(100)
    )
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction.id,
    )

    response_data = None

    # when
    create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    checkout.refresh_from_db()
    transaction.refresh_from_db()
    assert transaction.last_refund_success is False
    assert checkout.automatically_refundable is False


def test_create_event_from_request_and_webhook_error_response_calculate_refundable(
    transaction_item_generator,
    checkout,
    app,
):
    # given
    checkout.automatically_refundable = True
    checkout.save()

    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(100)
    )
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction.id,
    )

    event_amount = 12.00
    event_type = TransactionEventType.CHARGE_FAILURE
    event_time = "2022-11-18T13:25:58.169685+00:00"
    event_url = "http://localhost:3000/event/ref123"
    event_cause = "No cause"

    response_data = {
        # missing pspReference
        "amount": event_amount,
        "result": event_type.upper(),
        "time": event_time,
        "externalUrl": event_url,
        "message": event_cause,
        "actions": ["CHARGE", "CHARGE", "CANCEL"],
    }

    # when
    create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    checkout.refresh_from_db()
    transaction.refresh_from_db()
    assert transaction.last_refund_success is False
    assert checkout.automatically_refundable is False


def test_create_event_from_request_and_webhook_failure_event_calculate_refundable(
    transaction_item_generator,
    checkout,
    app,
):
    # given
    checkout.automatically_refundable = True
    checkout.save()

    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(100)
    )
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction.id,
    )

    event_amount = 11.00
    event_type = TransactionEventType.REFUND_FAILURE
    event_time = "2022-11-18T13:25:58.169685+00:00"
    event_url = "http://localhost:3000/event/ref123"
    event_cause = "No cause"

    response_data = {
        "pspReference": "123",
        "amount": event_amount,
        "result": event_type.upper(),
        "time": event_time,
        "externalUrl": event_url,
        "message": event_cause,
        "actions": ["CHARGE", "CHARGE", "CANCEL"],
    }

    # when
    create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    checkout.refresh_from_db()
    transaction.refresh_from_db()
    assert transaction.last_refund_success is False
    assert checkout.automatically_refundable is False


def test_create_event_from_request_and_webhook_success_event_calculate_refundable(
    transaction_item_generator,
    checkout,
    app,
):
    # given
    checkout.automatically_refundable = False
    checkout.save()

    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(100)
    )
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction.id,
    )

    event_amount = 12.00
    event_type = TransactionEventType.REFUND_SUCCESS
    event_time = "2022-11-18T13:25:58.169685+00:00"
    event_url = "http://localhost:3000/event/ref123"
    event_cause = "No cause"

    response_data = {
        "pspReference": "123",
        "amount": event_amount,
        "result": event_type.upper(),
        "time": event_time,
        "externalUrl": event_url,
        "message": event_cause,
        "actions": ["CHARGE", "CHARGE", "CANCEL"],
    }

    # when
    create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    checkout.refresh_from_db()
    transaction.refresh_from_db()
    assert transaction.last_refund_success is True
    assert checkout.automatically_refundable is True


@pytest.mark.parametrize(
    ("event_type", "expected_status"),
    [
        (TransactionEventType.REFUND_SUCCESS, OrderGrantedRefundStatus.SUCCESS),
        (TransactionEventType.REFUND_FAILURE, OrderGrantedRefundStatus.FAILURE),
    ],
)
def test_create_event_from_request_and_webhook_success_updated_granted_refund_status(
    event_type,
    expected_status,
    transaction_item_generator,
    order,
    app,
):
    # given
    transaction = transaction_item_generator(
        order_id=order.pk, charged_value=Decimal(100)
    )

    granted_refund = order.granted_refunds.create(
        amount_value=Decimal(100),
        currency="USD",
        transaction_item_id=transaction.id,
        status=OrderGrantedRefundStatus.NONE,
    )
    with freeze_time("2022-11-18T12:25:58"):
        request_event = TransactionEvent.objects.create(
            type=TransactionEventType.REFUND_REQUEST,
            amount_value=Decimal(11.00),
            currency="USD",
            transaction_id=transaction.id,
            related_granted_refund=granted_refund,
        )

    event_amount = 12.00
    event_type = event_type
    event_time = "2022-11-18T13:25:58.169685+00:00"
    event_url = "http://localhost:3000/event/ref123"
    event_cause = "No cause"

    response_data = {
        "pspReference": "123",
        "amount": event_amount,
        "result": event_type.upper(),
        "time": event_time,
        "externalUrl": event_url,
        "message": event_cause,
        "actions": ["CHARGE", "CHARGE", "CANCEL"],
    }

    # when
    create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    granted_refund.refresh_from_db()
    assert granted_refund.status == expected_status


def test_create_event_from_request_and_webhook_success_granted_refund_status_only_psp(
    transaction_item_generator,
    order,
    app,
):
    # given
    transaction = transaction_item_generator(
        order_id=order.pk, charged_value=Decimal(100)
    )

    granted_refund = order.granted_refunds.create(
        amount_value=Decimal(100),
        currency="USD",
        transaction_item_id=transaction.id,
        status=OrderGrantedRefundStatus.NONE,
    )
    with freeze_time("2022-11-18T12:25:58"):
        request_event = TransactionEvent.objects.create(
            type=TransactionEventType.REFUND_REQUEST,
            amount_value=Decimal(11.00),
            currency="USD",
            transaction_id=transaction.id,
            related_granted_refund=granted_refund,
        )

    response_data = {
        "pspReference": "123",
    }

    # when
    create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    granted_refund.refresh_from_db()
    assert granted_refund.status == OrderGrantedRefundStatus.PENDING


def test_create_event_from_request_and_webhook_pending_event_calculate_refundable(
    transaction_item_generator,
    checkout,
    app,
):
    # given
    checkout.automatically_refundable = False
    checkout.save()

    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(100)
    )
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction.id,
    )

    response_data = {
        "pspReference": "123",
    }

    # when
    create_transaction_event_from_request_and_webhook_response(
        request_event, app, response_data
    )

    # then
    checkout.refresh_from_db()
    transaction.refresh_from_db()
    assert transaction.last_refund_success is True
    assert checkout.automatically_refundable is True


@pytest.mark.parametrize(
    ("db_field_name", "value", "event_type"),
    [
        ("authorized_value", Decimal("12"), TransactionEventType.AUTHORIZATION_SUCCESS),
        ("charged_value", Decimal("13"), TransactionEventType.CHARGE_SUCCESS),
        ("canceled_value", Decimal("14"), TransactionEventType.CANCEL_SUCCESS),
        ("refunded_value", Decimal("15"), TransactionEventType.REFUND_SUCCESS),
    ],
)
def test_create_manual_adjustment_events_creates_calculation_events(
    db_field_name, value, event_type, transaction_item_generator, app
):
    # given
    transaction = transaction_item_generator(app=app)
    money_data = {db_field_name: value}

    # when
    create_manual_adjustment_events(
        transaction=transaction, money_data=money_data, app=app, user=None
    )

    # then
    event = transaction.events.filter(type=event_type).get()
    assert event.amount_value == value
    assert event.include_in_calculations is True


def test_create_manual_adjustment_events_additional_authorization(
    transaction_item_generator, app
):
    # given
    authorized_value = Decimal("10")
    transaction = transaction_item_generator(app=app, authorized_value=Decimal("2"))
    money_data = {"authorized_value": authorized_value}

    # when
    create_manual_adjustment_events(
        transaction=transaction, money_data=money_data, app=app, user=None
    )

    # then
    event = transaction.events.filter(
        type=TransactionEventType.AUTHORIZATION_ADJUSTMENT
    ).get()
    assert event.amount_value == authorized_value
    assert event.include_in_calculations is True


def test_create_manual_adjustment_events_additional_charge(
    transaction_item_generator, app
):
    # given
    charged_value = Decimal("10")
    current_charge_value = Decimal("2")
    transaction = transaction_item_generator(
        app=app, charged_value=current_charge_value
    )
    money_data = {"charged_value": charged_value}

    # when
    create_manual_adjustment_events(
        transaction=transaction, money_data=money_data, app=app, user=None
    )

    # then
    event = transaction.events.filter(type=TransactionEventType.CHARGE_SUCCESS).last()
    assert event.amount_value == charged_value - current_charge_value
    assert event.include_in_calculations is True


def test_create_manual_adjustment_events_additional_refund(
    transaction_item_generator, app
):
    # given
    refunded_value = Decimal("10")
    current_refunded_value = Decimal("2")
    transaction = transaction_item_generator(
        app=app, refunded_value=current_refunded_value
    )
    money_data = {"refunded_value": refunded_value}

    # when
    create_manual_adjustment_events(
        transaction=transaction, money_data=money_data, app=app, user=None
    )

    # then
    event = transaction.events.filter(type=TransactionEventType.REFUND_SUCCESS).last()
    assert event.amount_value == refunded_value - current_refunded_value
    assert event.include_in_calculations is True


def test_create_manual_adjustment_events_additional_cancel(
    transaction_item_generator, app
):
    # given
    canceled_value = Decimal("10")
    current_canceled_value = Decimal("2")
    transaction = transaction_item_generator(
        app=app, canceled_value=current_canceled_value
    )
    money_data = {"canceled_value": canceled_value}

    # when
    create_manual_adjustment_events(
        transaction=transaction, money_data=money_data, app=app, user=None
    )

    # then
    event = transaction.events.filter(type=TransactionEventType.CANCEL_SUCCESS).last()
    assert event.amount_value == canceled_value - current_canceled_value
    assert event.include_in_calculations is True


@pytest.mark.parametrize(
    ("request_type", "expected_events"),
    [
        (
            TransactionEventType.AUTHORIZATION_REQUEST,
            [
                TransactionEventType.AUTHORIZATION_FAILURE,
                TransactionEventType.AUTHORIZATION_ADJUSTMENT,
                TransactionEventType.AUTHORIZATION_SUCCESS,
            ],
        ),
        (
            TransactionEventType.CHARGE_REQUEST,
            [
                TransactionEventType.CHARGE_FAILURE,
                TransactionEventType.CHARGE_SUCCESS,
            ],
        ),
        (
            TransactionEventType.REFUND_REQUEST,
            [
                TransactionEventType.REFUND_FAILURE,
                TransactionEventType.REFUND_SUCCESS,
            ],
        ),
        (
            TransactionEventType.CANCEL_REQUEST,
            [
                TransactionEventType.CANCEL_FAILURE,
                TransactionEventType.CANCEL_SUCCESS,
            ],
        ),
    ],
)
def test_get_correct_event_types_based_on_request_type(request_type, expected_events):
    correct_types = get_correct_event_types_based_on_request_type(request_type)
    assert set(correct_types) == set(expected_events)


@pytest.mark.parametrize(
    ("response_result", "transaction_amount_field_name"),
    [
        (TransactionEventType.AUTHORIZATION_REQUEST, "authorize_pending_value"),
        (TransactionEventType.AUTHORIZATION_SUCCESS, "authorized_value"),
        (TransactionEventType.CHARGE_REQUEST, "charge_pending_value"),
        (TransactionEventType.CHARGE_SUCCESS, "charged_value"),
    ],
)
def test_create_transaction_event_for_transaction_session_success_response(
    response_result,
    transaction_amount_field_name,
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
):
    # given
    expected_amount = Decimal("15")
    response = transaction_session_response.copy()
    response["result"] = response_result.upper()
    response["amount"] = expected_amount
    transaction = transaction_item_generator()
    request_event = TransactionEvent.objects.create(
        transaction=transaction, include_in_calculations=False
    )
    # when
    response_event = create_transaction_event_for_transaction_session(
        request_event,
        webhook_app,
        manager=plugins_manager,
        transaction_webhook_response=response,
    )

    # then
    assert response_event.include_in_calculations
    assert response_event.amount_value == expected_amount
    transaction.refresh_from_db()
    assert getattr(transaction, transaction_amount_field_name) == expected_amount


@pytest.mark.parametrize(
    ("response_result", "transaction_amount_field_name"),
    [
        (TransactionEventType.AUTHORIZATION_REQUEST, "authorize_pending_value"),
        (TransactionEventType.AUTHORIZATION_SUCCESS, "authorized_value"),
        (TransactionEventType.CHARGE_REQUEST, "charge_pending_value"),
        (TransactionEventType.CHARGE_SUCCESS, "charged_value"),
    ],
)
def test_create_transaction_event_for_transaction_session_success_response_with_0(
    response_result,
    transaction_amount_field_name,
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
):
    # given
    expected_amount = Decimal("0")
    response = transaction_session_response.copy()
    response["result"] = response_result.upper()
    response["amount"] = expected_amount
    transaction = transaction_item_generator()
    request_event = TransactionEvent.objects.create(
        transaction=transaction, include_in_calculations=False
    )
    # when
    response_event = create_transaction_event_for_transaction_session(
        request_event,
        webhook_app,
        manager=plugins_manager,
        transaction_webhook_response=response,
    )

    # then
    assert response_event.include_in_calculations
    assert response_event.amount_value == expected_amount
    transaction.refresh_from_db()
    assert getattr(transaction, transaction_amount_field_name) == expected_amount


@pytest.mark.parametrize(
    "response_result",
    [
        TransactionEventType.AUTHORIZATION_ACTION_REQUIRED,
        TransactionEventType.CHARGE_ACTION_REQUIRED,
        TransactionEventType.AUTHORIZATION_FAILURE,
        TransactionEventType.CHARGE_FAILURE,
        TransactionEventType.REFUND_FAILURE,
        TransactionEventType.REFUND_SUCCESS,
    ],
)
def test_create_transaction_event_for_transaction_session_not_success_events(
    response_result,
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
):
    # given
    expected_amount = Decimal("15")
    response = transaction_session_response.copy()
    response["result"] = response_result.upper()
    response["amount"] = expected_amount
    transaction = transaction_item_generator()
    request_event = TransactionEvent.objects.create(
        transaction=transaction,
        include_in_calculations=False,
        amount_value=expected_amount,
        type=TransactionEventType.CHARGE_REQUEST,
    )
    # when
    response_event = create_transaction_event_for_transaction_session(
        request_event,
        webhook_app,
        manager=plugins_manager,
        transaction_webhook_response=response,
    )

    # then
    assert response_event.amount_value == expected_amount
    assert response_event.type in [response_result, TransactionEventType.CHARGE_FAILURE]
    transaction.refresh_from_db()
    assert transaction.authorized_value == Decimal("0")
    assert transaction.charged_value == Decimal("0")
    assert transaction.authorize_pending_value == Decimal("0")
    assert transaction.charge_pending_value == Decimal("0")


@pytest.mark.parametrize(
    ("response_result", "message"),
    [
        (
            TransactionEventType.AUTHORIZATION_SUCCESS,
            "Providing `pspReference` is required for AUTHORIZATION_SUCCESS.",
        ),
        (
            TransactionEventType.CHARGE_SUCCESS,
            "Providing `pspReference` is required for CHARGE_SUCCESS.",
        ),
        (
            TransactionEventType.CHARGE_FAILURE,
            "Message related to the payment",
        ),
        (
            TransactionEventType.CHARGE_REQUEST,
            "Providing `pspReference` is required for CHARGE_REQUEST.",
        ),
        (
            TransactionEventType.AUTHORIZATION_REQUEST,
            "Providing `pspReference` is required for AUTHORIZATION_REQUEST.",
        ),
    ],
)
def test_create_transaction_event_for_transaction_session_missing_psp_reference(
    response_result,
    message,
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
):
    # given
    expected_amount = Decimal("15")
    response = transaction_session_response.copy()
    response["result"] = response_result.upper()
    response["amount"] = expected_amount
    del response["pspReference"]
    transaction = transaction_item_generator()
    request_event = TransactionEvent.objects.create(
        transaction=transaction,
        include_in_calculations=False,
        amount_value=expected_amount,
        type=TransactionEventType.CHARGE_REQUEST,
    )
    # when
    response_event = create_transaction_event_for_transaction_session(
        request_event,
        webhook_app,
        manager=plugins_manager,
        transaction_webhook_response=response,
    )

    # then
    assert response_event.amount_value == expected_amount
    assert response_event.type == TransactionEventType.CHARGE_FAILURE
    assert response_event.message == message
    transaction.refresh_from_db()
    assert transaction.authorized_value == Decimal("0")
    assert transaction.charged_value == Decimal("0")
    assert transaction.authorize_pending_value == Decimal("0")
    assert transaction.charge_pending_value == Decimal("0")


@pytest.mark.parametrize(
    "response_result",
    [
        TransactionEventType.AUTHORIZATION_ACTION_REQUIRED,
        TransactionEventType.CHARGE_ACTION_REQUIRED,
    ],
)
def test_create_transaction_event_for_transaction_session_missing_reference_with_action(
    response_result,
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
):
    # given
    expected_amount = Decimal("15")
    response = transaction_session_response.copy()
    response["result"] = response_result.upper()
    response["amount"] = expected_amount
    del response["pspReference"]
    transaction = transaction_item_generator()
    request_event = TransactionEvent.objects.create(
        transaction=transaction,
        include_in_calculations=False,
        amount_value=expected_amount,
        type=TransactionEventType.CHARGE_REQUEST,
    )
    # when
    response_event = create_transaction_event_for_transaction_session(
        request_event,
        webhook_app,
        manager=plugins_manager,
        transaction_webhook_response=response,
    )

    # then
    assert response_event.amount_value == expected_amount
    assert response_event.type == response_result
    transaction.refresh_from_db()
    assert transaction.authorized_value == Decimal("0")
    assert transaction.charged_value == Decimal("0")
    assert transaction.authorize_pending_value == Decimal("0")
    assert transaction.charge_pending_value == Decimal("0")


@pytest.mark.parametrize(
    "response_result",
    [
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.CHARGE_SUCCESS,
    ],
)
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_create_transaction_event_for_transaction_session_call_webhook_order_updated(
    mock_order_fully_paid,
    mock_order_updated,
    response_result,
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
    order_with_lines,
    django_capture_on_commit_callbacks,
):
    # given
    expected_amount = Decimal("15")
    response = transaction_session_response.copy()
    response["result"] = response_result.upper()
    response["amount"] = expected_amount
    transaction = transaction_item_generator(order_id=order_with_lines.pk)
    request_event = TransactionEvent.objects.create(
        transaction=transaction, include_in_calculations=False
    )
    # when
    with django_capture_on_commit_callbacks(execute=True):
        create_transaction_event_for_transaction_session(
            request_event,
            webhook_app,
            manager=plugins_manager,
            transaction_webhook_response=response,
        )

    # then
    order_with_lines.refresh_from_db()
    assert not mock_order_fully_paid.called
    mock_order_updated.assert_called_once_with(order_with_lines, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_create_transaction_event_for_transaction_session_call_webhook_for_fully_paid(
    mock_order_fully_paid,
    mock_order_updated,
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
    order_with_lines,
    django_capture_on_commit_callbacks,
):
    # given
    response = transaction_session_response.copy()
    response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    response["amount"] = order_with_lines.total.gross.amount
    transaction = transaction_item_generator(order_id=order_with_lines.pk)
    request_event = TransactionEvent.objects.create(
        transaction=transaction, include_in_calculations=False
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        create_transaction_event_for_transaction_session(
            request_event,
            webhook_app,
            manager=plugins_manager,
            transaction_webhook_response=response,
        )

    # then
    order_with_lines.refresh_from_db()
    mock_order_fully_paid.assert_called_once_with(order_with_lines, webhooks=set())
    mock_order_updated.assert_called_once_with(order_with_lines, webhooks=set())


@pytest.mark.parametrize(
    "response_result,",
    [
        (TransactionEventType.AUTHORIZATION_REQUEST),
        (TransactionEventType.AUTHORIZATION_SUCCESS),
        (TransactionEventType.CHARGE_REQUEST),
        (TransactionEventType.CHARGE_SUCCESS),
    ],
)
def test_create_transaction_event_for_transaction_session_success_sets_actions(
    response_result,
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
):
    # given
    expected_amount = Decimal("15")
    response = transaction_session_response.copy()
    response["result"] = response_result.upper()
    response["amount"] = expected_amount
    response["actions"] = ["CANCEL", "CANCEL", "CHARGE", "REFUND"]

    transaction = transaction_item_generator()
    request_event = TransactionEvent.objects.create(
        transaction=transaction, include_in_calculations=False
    )

    # when
    create_transaction_event_for_transaction_session(
        request_event,
        webhook_app,
        manager=plugins_manager,
        transaction_webhook_response=response,
    )

    # then
    transaction.refresh_from_db()
    assert len(transaction.available_actions) == 3
    assert set(transaction.available_actions) == {"refund", "charge", "cancel"}


@pytest.mark.parametrize(
    "response_result",
    [
        TransactionEventType.AUTHORIZATION_ACTION_REQUIRED,
        TransactionEventType.CHARGE_ACTION_REQUIRED,
        TransactionEventType.AUTHORIZATION_FAILURE,
        TransactionEventType.CHARGE_FAILURE,
        TransactionEventType.REFUND_FAILURE,
        TransactionEventType.REFUND_SUCCESS,
    ],
)
def test_create_transaction_event_for_transaction_session_failure_doesnt_set_actions(
    response_result,
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
):
    # given
    expected_amount = Decimal("15")
    response = transaction_session_response.copy()
    response["result"] = response_result.upper()
    response["amount"] = expected_amount
    response["actions"] = ["CANCEL", "CHARGE", "REFUND"]
    transaction = transaction_item_generator(available_actions=["charge"])
    request_event = TransactionEvent.objects.create(
        transaction=transaction,
        include_in_calculations=False,
        amount_value=expected_amount,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    # when
    create_transaction_event_for_transaction_session(
        request_event,
        webhook_app,
        manager=plugins_manager,
        transaction_webhook_response=response,
    )

    # then
    transaction.refresh_from_db()
    assert transaction.available_actions == ["charge"]


@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_from_request_and_webhook_updates_modified_at(
    transaction_item_generator,
    checkout,
    app,
):
    # given
    transaction = transaction_item_generator(checkout_id=checkout.pk)
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction.id,
    )

    event_amount = 12.00
    event_type = TransactionEventType.CHARGE_FAILURE
    event_time = "2022-11-18T13:25:58.169685+00:00"
    event_url = "http://localhost:3000/event/ref123"
    event_cause = "No cause"

    expected_psp_reference = "psp:122:222"

    response_data = {
        "pspReference": expected_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
        "time": event_time,
        "externalUrl": event_url,
        "message": event_cause,
        "actions": ["CHARGE", "CHARGE", "CANCEL"],
    }

    # when
    with freeze_time("2023-03-18 12:00:00"):
        calculation_time = datetime.datetime.now(tz=datetime.UTC)
        create_transaction_event_from_request_and_webhook_response(
            request_event, app, response_data
        )

    # then
    transaction.refresh_from_db()
    checkout.refresh_from_db()
    assert transaction.modified_at == calculation_time
    assert checkout.last_transaction_modified_at == calculation_time


@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_updates_transaction_modified_at(
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
    checkout,
):
    # given
    expected_amount = Decimal("15")
    response = transaction_session_response.copy()
    response["amount"] = expected_amount

    transaction = transaction_item_generator(checkout_id=checkout.pk)
    request_event = TransactionEvent.objects.create(
        transaction=transaction, include_in_calculations=False
    )

    # when
    with freeze_time("2023-03-18 12:00:00"):
        calculation_time = datetime.datetime.now(tz=datetime.UTC)
        create_transaction_event_for_transaction_session(
            request_event,
            webhook_app,
            manager=plugins_manager,
            transaction_webhook_response=response,
        )

    # then
    transaction.refresh_from_db()
    checkout.refresh_from_db()
    assert transaction.modified_at == calculation_time
    assert checkout.last_transaction_modified_at == calculation_time


def test_create_transaction_event_for_transaction_session_failure_set_psp_reference(
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
):
    # given
    expected_psp_reference = "ABC"
    expected_amount = Decimal("15")
    response = transaction_session_response.copy()
    response["result"] = TransactionEventType.CHARGE_FAILURE.upper()
    response["amount"] = expected_amount
    response["pspReference"] = expected_psp_reference

    transaction = transaction_item_generator(available_actions=["charge"])
    request_event = TransactionEvent.objects.create(
        transaction=transaction,
        include_in_calculations=False,
        amount_value=expected_amount,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    # when
    create_transaction_event_for_transaction_session(
        request_event,
        webhook_app,
        manager=plugins_manager,
        transaction_webhook_response=response,
    )

    # then
    transaction.refresh_from_db()
    assert transaction.events.count() == 2
    failure_event = transaction.events.last()
    assert failure_event.psp_reference == expected_psp_reference
    assert failure_event.type == TransactionEventType.CHARGE_FAILURE
    assert transaction.psp_reference == expected_psp_reference


def test_create_transaction_event_for_transaction_session_when_psp_ref_missing(
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
):
    # given
    expected_amount = Decimal("15")
    response = transaction_session_response.copy()
    response["result"] = TransactionEventType.CHARGE_ACTION_REQUIRED.upper()
    response["amount"] = expected_amount
    response["pspReference"] = None

    transaction = transaction_item_generator(available_actions=["charge"])
    current_psp_reference = transaction.psp_reference
    request_event = TransactionEvent.objects.create(
        transaction=transaction,
        include_in_calculations=False,
        amount_value=expected_amount,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    # when
    create_transaction_event_for_transaction_session(
        request_event,
        webhook_app,
        manager=plugins_manager,
        transaction_webhook_response=response,
    )

    # then
    transaction.refresh_from_db()
    assert transaction.events.count() == 2
    assert transaction.psp_reference == current_psp_reference


@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_updates_transaction_modified_at_for_failure(
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
    checkout,
):
    # given
    expected_amount = Decimal("15")
    response = transaction_session_response.copy()
    response["amount"] = expected_amount
    response["result"] = TransactionEventType.CHARGE_FAILURE.upper()

    transaction = transaction_item_generator(checkout_id=checkout.pk)
    request_event = TransactionEvent.objects.create(
        transaction=transaction, include_in_calculations=False
    )

    # when
    with freeze_time("2023-03-18 12:00:00"):
        calculation_time = datetime.datetime.now(tz=datetime.UTC)
        create_transaction_event_for_transaction_session(
            request_event,
            webhook_app,
            manager=plugins_manager,
            transaction_webhook_response=response,
        )

    # then
    transaction.refresh_from_db()
    checkout.refresh_from_db()
    assert transaction.modified_at == calculation_time
    assert checkout.last_transaction_modified_at == calculation_time


def test_recalculate_refundable_for_checkout_with_request_refund(
    transaction_item_generator, checkout
):
    # given
    checkout.automatically_refundable = True
    checkout.save(update_fields=["automatically_refundable"])

    transaction_item = transaction_item_generator(
        checkout_id=checkout.pk, last_refund_success=True, charged_value=Decimal(10)
    )
    request_event = transaction_item.events.create(
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=Decimal(10),
        include_in_calculations=False,
    )

    # when
    recalculate_refundable_for_checkout(transaction_item, request_event)

    # then
    checkout.refresh_from_db()
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is False
    assert checkout.automatically_refundable is False


def test_recalculate_refundable_for_checkout_with_request_cancel(
    transaction_item_generator, checkout
):
    # given
    checkout.automatically_refundable = True
    checkout.save(update_fields=["automatically_refundable"])

    transaction_item = transaction_item_generator(
        checkout_id=checkout.pk, last_refund_success=True, charged_value=Decimal(10)
    )
    request_event = transaction_item.events.create(
        type=TransactionEventType.CANCEL_REQUEST,
        amount_value=Decimal(10),
        include_in_calculations=False,
    )

    # when
    recalculate_refundable_for_checkout(transaction_item, request_event)

    # then
    checkout.refresh_from_db()
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is False
    assert checkout.automatically_refundable is False


@pytest.mark.parametrize(
    "event_type",
    [
        TransactionEventType.AUTHORIZATION_REQUEST,
        TransactionEventType.CHARGE_REQUEST,
    ],
)
def test_recalculate_refundable_for_checkout_with_non_related_request_event(
    event_type, transaction_item_generator, checkout
):
    # given
    checkout.automatically_refundable = True
    checkout.save(update_fields=["automatically_refundable"])

    transaction_item = transaction_item_generator(
        checkout_id=checkout.pk, last_refund_success=True, charged_value=Decimal(10)
    )
    request_event = transaction_item.events.create(
        type=event_type,
        amount_value=Decimal(10),
        include_in_calculations=False,
    )

    # when
    recalculate_refundable_for_checkout(transaction_item, request_event)

    # then
    checkout.refresh_from_db()
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is True
    assert checkout.automatically_refundable is True


@pytest.mark.parametrize(
    "event_type",
    [
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.AUTHORIZATION_FAILURE,
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.CHARGE_FAILURE,
    ],
)
def test_recalculate_refundable_for_checkout_with_non_related_events(
    event_type, transaction_item_generator, checkout
):
    # given
    checkout.automatically_refundable = True
    checkout.save(update_fields=["automatically_refundable"])

    transaction_item = transaction_item_generator(
        checkout_id=checkout.pk, last_refund_success=True, charged_value=Decimal(10)
    )
    request_event = transaction_item.events.create(
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=Decimal(10),
        include_in_calculations=False,
        psp_reference="123",
    )
    response_event = transaction_item.events.create(
        type=event_type, amount_value=Decimal(10), psp_reference="123"
    )

    # when
    recalculate_refundable_for_checkout(transaction_item, request_event, response_event)

    # then
    checkout.refresh_from_db()
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is True
    assert checkout.automatically_refundable is True


def test_recalculate_refundable_for_checkout_with_response_refund_success(
    transaction_item_generator, checkout
):
    # given
    checkout.automatically_refundable = False
    checkout.save(update_fields=["automatically_refundable"])

    transaction_item = transaction_item_generator(
        checkout_id=checkout.pk, last_refund_success=False, charged_value=Decimal(10)
    )
    request_event = transaction_item.events.create(
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=Decimal(10),
        include_in_calculations=False,
        psp_reference="123",
    )
    response_event = transaction_item.events.create(
        type=TransactionEventType.REFUND_SUCCESS,
        amount_value=Decimal(10),
        psp_reference="123",
    )

    # when
    recalculate_refundable_for_checkout(transaction_item, request_event, response_event)

    # then
    checkout.refresh_from_db()
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is True
    assert checkout.automatically_refundable is True


def test_recalculate_refundable_for_checkout_with_response_refund_failure(
    transaction_item_generator, checkout
):
    # given
    checkout.automatically_refundable = True
    checkout.save(update_fields=["automatically_refundable"])

    transaction_item = transaction_item_generator(
        checkout_id=checkout.pk, last_refund_success=True, charged_value=Decimal(10)
    )
    request_event = transaction_item.events.create(
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=Decimal(10),
        include_in_calculations=False,
        psp_reference="123",
    )
    response_event = transaction_item.events.create(
        type=TransactionEventType.REFUND_FAILURE,
        amount_value=Decimal(10),
        psp_reference="123",
    )

    # when
    recalculate_refundable_for_checkout(transaction_item, request_event, response_event)

    # then
    checkout.refresh_from_db()
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is False
    assert checkout.automatically_refundable is False


def test_recalculate_refundable_for_checkout_with_response_refund_pending(
    transaction_item_generator, checkout
):
    # given
    checkout.automatically_refundable = False
    checkout.save(update_fields=["automatically_refundable"])

    transaction_item = transaction_item_generator(
        checkout_id=checkout.pk, last_refund_success=False, charged_value=Decimal(10)
    )
    request_event = transaction_item.events.create(
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=Decimal(10),
        include_in_calculations=True,
        psp_reference="123",
    )

    # when
    recalculate_refundable_for_checkout(transaction_item, request_event)

    # then
    checkout.refresh_from_db()
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is True
    assert checkout.automatically_refundable is True


def test_recalculate_refundable_for_checkout_with_response_cancel_failure(
    transaction_item_generator, checkout
):
    # given
    checkout.automatically_refundable = True
    checkout.save(update_fields=["automatically_refundable"])

    transaction_item = transaction_item_generator(
        checkout_id=checkout.pk, last_refund_success=True, charged_value=Decimal(10)
    )
    request_event = transaction_item.events.create(
        type=TransactionEventType.CANCEL_REQUEST,
        amount_value=Decimal(10),
        include_in_calculations=False,
        psp_reference="123",
    )
    response_event = transaction_item.events.create(
        type=TransactionEventType.CANCEL_FAILURE,
        amount_value=Decimal(10),
        psp_reference="123",
    )

    # when
    recalculate_refundable_for_checkout(transaction_item, request_event, response_event)

    # then
    checkout.refresh_from_db()
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is False
    assert checkout.automatically_refundable is False


def test_recalculate_refundable_for_checkout_with_response_cancel_success(
    transaction_item_generator, checkout
):
    # given
    checkout.automatically_refundable = False
    checkout.save(update_fields=["automatically_refundable"])

    transaction_item = transaction_item_generator(
        checkout_id=checkout.pk, last_refund_success=False, charged_value=Decimal(10)
    )
    request_event = transaction_item.events.create(
        type=TransactionEventType.CANCEL_REQUEST,
        amount_value=Decimal(10),
        include_in_calculations=False,
        psp_reference="123",
    )
    response_event = transaction_item.events.create(
        type=TransactionEventType.CANCEL_SUCCESS,
        amount_value=Decimal(10),
        psp_reference="123",
    )

    # when
    recalculate_refundable_for_checkout(transaction_item, request_event, response_event)

    # then
    checkout.refresh_from_db()
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is True
    assert checkout.automatically_refundable is True


def test_recalculate_refundable_for_checkout_with_response_cancel_pending(
    transaction_item_generator, checkout
):
    # given
    checkout.automatically_refundable = False
    checkout.save(update_fields=["automatically_refundable"])

    transaction_item = transaction_item_generator(
        checkout_id=checkout.pk, last_refund_success=False, charged_value=Decimal(10)
    )
    request_event = transaction_item.events.create(
        type=TransactionEventType.CANCEL_REQUEST,
        amount_value=Decimal(10),
        include_in_calculations=True,
        psp_reference="123",
    )

    # when
    recalculate_refundable_for_checkout(transaction_item, request_event)

    # then
    checkout.refresh_from_db()
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is True
    assert checkout.automatically_refundable is True


def test_recalculate_refundable_for_checkout_update_missing_checkout(
    transaction_item_generator,
):
    # given
    transaction_item = transaction_item_generator(
        last_refund_success=True, charged_value=Decimal(10)
    )
    request_event = transaction_item.events.create(
        type=TransactionEventType.CANCEL_REQUEST,
        amount_value=Decimal(10),
        include_in_calculations=False,
        psp_reference="123",
    )

    # when
    recalculate_refundable_for_checkout(transaction_item, request_event)

    # then
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is False


@pytest.mark.parametrize(
    ("input_event_type", "event_type_to_create"),
    [
        (TransactionEventType.CHARGE_FAILURE, TransactionEventType.CHARGE_SUCCESS),
        (TransactionEventType.CHARGE_FAILURE, TransactionEventType.CHARGE_REQUEST),
        (
            TransactionEventType.CHARGE_FAILURE,
            TransactionEventType.AUTHORIZATION_SUCCESS,
        ),
        (
            TransactionEventType.CHARGE_FAILURE,
            TransactionEventType.AUTHORIZATION_REQUEST,
        ),
        (
            TransactionEventType.CHARGE_FAILURE,
            TransactionEventType.AUTHORIZATION_FAILURE,
        ),
        (TransactionEventType.REFUND_FAILURE, TransactionEventType.REFUND_SUCCESS),
        (TransactionEventType.REFUND_FAILURE, TransactionEventType.REFUND_REQUEST),
        (TransactionEventType.REFUND_FAILURE, TransactionEventType.CHARGE_SUCCESS),
        (TransactionEventType.REFUND_FAILURE, TransactionEventType.CHARGE_REQUEST),
        (TransactionEventType.REFUND_FAILURE, TransactionEventType.CHARGE_FAILURE),
        (TransactionEventType.CANCEL_FAILURE, TransactionEventType.CANCEL_SUCCESS),
        (TransactionEventType.CANCEL_FAILURE, TransactionEventType.CANCEL_REQUEST),
        (
            TransactionEventType.CANCEL_FAILURE,
            TransactionEventType.AUTHORIZATION_SUCCESS,
        ),
        (
            TransactionEventType.CANCEL_FAILURE,
            TransactionEventType.AUTHORIZATION_REQUEST,
        ),
        (
            TransactionEventType.CANCEL_FAILURE,
            TransactionEventType.AUTHORIZATION_FAILURE,
        ),
        (
            TransactionEventType.AUTHORIZATION_FAILURE,
            TransactionEventType.AUTHORIZATION_SUCCESS,
        ),
        (
            TransactionEventType.AUTHORIZATION_FAILURE,
            TransactionEventType.AUTHORIZATION_REQUEST,
        ),
        (TransactionEventType.REFUND_REVERSE, TransactionEventType.REFUND_SUCCESS),
        (TransactionEventType.CHARGE_BACK, TransactionEventType.CHARGE_SUCCESS),
    ],
)
def test_get_transaction_event_amount(
    input_event_type,
    event_type_to_create,
    transaction_events_generator,
    transaction_item,
):
    # given
    expected_amount = 10
    psp_reference = "xyz"
    transaction_events_generator(
        transaction=transaction_item,
        psp_references=[
            psp_reference,
        ],
        types=[
            event_type_to_create,
        ],
        amounts=[
            expected_amount,
        ],
    )

    # when
    amount = get_transaction_event_amount(input_event_type, psp_reference)

    # then
    assert amount == expected_amount


def test_get_transaction_event_amount_match_the_newest_event(
    transaction_events_generator, transaction_item
):
    # given
    psp_reference = "xyz"
    event_types = [
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.CHARGE_REQUEST,
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.AUTHORIZATION_REQUEST,
        TransactionEventType.AUTHORIZATION_FAILURE,
    ]
    events = transaction_events_generator(
        transaction=transaction_item,
        psp_references=[
            psp_reference,
        ]
        * len(event_types),
        types=event_types,
        amounts=[10, 5, 4, 3, 2],
    )
    newest_event = events[-1]
    for event in events[:-1]:
        event.created_at = newest_event.created_at - datetime.timedelta(minutes=10)
    TransactionEvent.objects.bulk_update(events[:-1], ["created_at"])

    # when
    amount = get_transaction_event_amount(
        TransactionEventType.CHARGE_FAILURE, psp_reference
    )

    # then
    assert amount == newest_event.amount_value


@pytest.mark.parametrize(
    ("input_event_type", "event_types_to_create"),
    [
        (TransactionEventType.CHARGE_FAILURE, [TransactionEventType.REFUND_FAILURE]),
        (TransactionEventType.CHARGE_FAILURE, []),
        (
            TransactionEventType.REFUND_FAILURE,
            [TransactionEventType.AUTHORIZATION_FAILURE],
        ),
        (TransactionEventType.REFUND_FAILURE, []),
        (TransactionEventType.CANCEL_FAILURE, [TransactionEventType.CHARGE_FAILURE]),
        (TransactionEventType.CANCEL_FAILURE, []),
        (
            TransactionEventType.AUTHORIZATION_FAILURE,
            [TransactionEventType.CHARGE_SUCCESS],
        ),
        (TransactionEventType.AUTHORIZATION_FAILURE, []),
        (TransactionEventType.REFUND_REVERSE, [TransactionEventType.REFUND_FAILURE]),
        (TransactionEventType.REFUND_REVERSE, []),
        (TransactionEventType.CHARGE_BACK, [TransactionEventType.CHARGE_FAILURE]),
        (TransactionEventType.CHARGE_BACK, []),
    ],
)
def test_get_transaction_event_amount_missing_matching_event(
    input_event_type,
    event_types_to_create,
    transaction_events_generator,
    transaction_item,
):
    # given
    amount = 10
    psp_reference = "xyz"
    if event_types_to_create:
        transaction_events_generator(
            transaction=transaction_item,
            psp_references=[
                psp_reference,
            ],
            types=event_types_to_create,
            amounts=[
                amount,
            ],
        )

    # when & then
    with pytest.raises(
        ValueError, match=f"Unable to deduce the amount for {input_event_type} event."
    ):
        get_transaction_event_amount(input_event_type, psp_reference)


def test_get_transaction_event_amount_missing_matching_event_different_psp_reference(
    transaction_events_generator, transaction_item
):
    # given
    psp_reference = "xyz"
    transaction_events_generator(
        transaction=transaction_item,
        psp_references=[
            "123",
        ],
        types=[TransactionEventType.CHARGE_SUCCESS],
        amounts=[10],
    )
    event_type = TransactionEventType.CHARGE_FAILURE

    # when & then
    with pytest.raises(
        ValueError, match=f"Unable to deduce the amount for {event_type} event."
    ):
        get_transaction_event_amount(event_type, psp_reference)


def test_get_transaction_event_amount_invalid_event_type(
    transaction_events_generator, transaction_item
):
    # given
    psp_reference = "xyz"
    transaction_events_generator(
        transaction=transaction_item,
        psp_references=[
            psp_reference,
        ],
        types=[TransactionEventType.CHARGE_FAILURE],
        amounts=[10],
    )
    event_type = TransactionEventType.CHARGE_SUCCESS

    # when & then
    with pytest.raises(
        ValueError, match=f"Unable to deduce the amount for {event_type} event."
    ):
        get_transaction_event_amount(event_type, psp_reference)


def test_get_transaction_event_amount_for_info_event_type(
    transaction_events_generator, transaction_item
):
    # given
    psp_reference = "xyz"
    transaction_events_generator(
        transaction=transaction_item,
        psp_references=[
            "123",
        ],
        types=[TransactionEventType.CHARGE_SUCCESS],
        amounts=[10],
    )

    # when
    amount = get_transaction_event_amount(TransactionEventType.INFO, psp_reference)

    # then
    assert amount == 0


def test_deduplicate_event(transaction_events_generator, transaction_item, app):
    # given
    event = TransactionEvent(
        psp_reference="psp:123",
        type=TransactionEventType.CHARGE_SUCCESS,
        amount_value=Decimal("10"),
        transaction=transaction_item,
        currency=transaction_item.currency,
    )

    # when
    result_event, err_msg = deduplicate_event(event, app)

    # then
    assert err_msg is None
    assert result_event


def test_deduplicate_event_different_amount(
    transaction_events_generator, transaction_item, app, caplog
):
    # given
    events = transaction_events_generator(
        psp_references=["psp:123"],
        types=[TransactionEventType.CHARGE_SUCCESS],
        amounts=[Decimal("10")],
        transaction=transaction_item,
    )
    event = TransactionEvent(
        psp_reference="psp:123",
        type=TransactionEventType.CHARGE_SUCCESS,
        amount_value=Decimal("12"),
        transaction=transaction_item,
        currency=transaction_item.currency,
    )

    # when
    result_event, err_msg = deduplicate_event(event, app)

    # then
    assert result_event.id == events[0].id
    assert err_msg == (
        "The transaction with provided `pspReference` and "
        "`type` already exists with different amount."
    )
    assert caplog.records[0].levelno == logging.WARNING
    assert caplog.records[0].message == err_msg


def test_deduplicate_event_authorization_already_exists(
    transaction_events_generator, transaction_item, app, caplog
):
    # given
    transaction_events_generator(
        psp_references=["psp:123"],
        types=[TransactionEventType.AUTHORIZATION_SUCCESS],
        amounts=[Decimal("10")],
        transaction=transaction_item,
    )
    event = TransactionEvent(
        psp_reference="psp:111",
        type=TransactionEventType.AUTHORIZATION_SUCCESS,
        amount_value=Decimal("10"),
        transaction=transaction_item,
        currency=transaction_item.currency,
    )

    # when
    result_event, err_msg = deduplicate_event(event, app)

    # then
    assert result_event
    assert err_msg == (
        "Event with `AUTHORIZATION_SUCCESS` already "
        "reported for the transaction. Use "
        "`AUTHORIZATION_ADJUSTMENT` to change the "
        "authorization amount."
    )
    assert caplog.records[0].levelno == logging.WARNING
    assert caplog.records[0].message == err_msg
