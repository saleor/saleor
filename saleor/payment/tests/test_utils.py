from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from django.utils import timezone
from freezegun import freeze_time

from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
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
    create_payment_lines_information,
    create_transaction_event_from_request_and_webhook_response,
    get_channel_slug_from_payment,
    parse_transaction_action_data,
    try_void_or_refund_inactive_payment,
)


def test_create_payment_lines_information_order(payment_dummy):
    # given
    manager = get_plugins_manager()

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
    manager = get_plugins_manager()

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


def get_expected_checkout_payment_lines(
    manager, checkout_info, lines, address, discounts
):
    expected_payment_lines = []

    for line_info in lines:
        unit_gross = manager.calculate_checkout_line_unit_price(
            checkout_info,
            lines,
            line_info,
            address,
            discounts,
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
        discounts=discounts,
    ).gross.amount

    return PaymentLinesData(
        lines=expected_payment_lines,
        shipping_amount=shipping_gross,
        voucher_amount=Decimal("0.00"),
    )


def test_create_payment_lines_information_checkout(payment_dummy, checkout_with_items):
    # given
    manager = get_plugins_manager()
    payment_dummy.order = None
    payment_dummy.checkout = checkout_with_items

    # when
    payment_lines = create_payment_lines_information(payment_dummy, manager)

    # then
    lines, _ = fetch_checkout_lines(checkout_with_items)
    discounts = []
    checkout_info = fetch_checkout_info(checkout_with_items, lines, discounts, manager)
    address = checkout_with_items.shipping_address
    expected_payment_lines = get_expected_checkout_payment_lines(
        manager, checkout_info, lines, address, discounts
    )

    assert payment_lines == expected_payment_lines


def test_create_payment_lines_information_checkout_with_voucher(
    payment_dummy, checkout_with_items
):
    # given
    manager = get_plugins_manager()
    voucher_amount = Decimal("12.30")
    payment_dummy.order = None
    checkout_with_items.discount_amount = voucher_amount
    payment_dummy.checkout = checkout_with_items

    # when
    payment_lines = create_payment_lines_information(payment_dummy, manager)

    # then
    lines, _ = fetch_checkout_lines(checkout_with_items)
    discounts = []
    checkout_info = fetch_checkout_info(checkout_with_items, lines, discounts, manager)
    address = checkout_with_items.shipping_address
    expected_payment_lines_data = get_expected_checkout_payment_lines(
        manager, checkout_info, lines, address, discounts
    )

    expected_payment_lines_data.voucher_amount = -voucher_amount

    assert payment_lines == expected_payment_lines_data


def test_create_payment_lines_information_invalid_payment(payment_dummy):
    # given
    manager = get_plugins_manager()
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


def test_get_channel_slug_from_payment_without_checkout_and_order(
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
    parsed_data = parse_transaction_action_data(response_data)

    # then
    assert isinstance(parsed_data, TransactionRequestResponse)

    assert parsed_data.psp_reference == expected_psp_reference
    assert parsed_data.event is None


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
        "event": {
            "amount": event_amount,
            "type": event_type.upper(),
            "time": event_time,
            "externalUrl": event_url,
            "message": event_cause,
        },
    }

    # when
    parsed_data = parse_transaction_action_data(response_data)

    # then
    assert isinstance(parsed_data, TransactionRequestResponse)

    assert parsed_data.psp_reference == expected_psp_reference
    assert isinstance(parsed_data.event, TransactionRequestEventResponse)
    assert parsed_data.event.psp_reference == expected_psp_reference
    assert parsed_data.event.amount == event_amount
    assert parsed_data.event.time == datetime.fromisoformat(event_time)
    assert parsed_data.event.external_url == event_url
    assert parsed_data.event.message == event_cause
    assert parsed_data.event.type == event_type


@freeze_time("2018-05-31 12:00:01")
def test_parse_transaction_action_data_with_event_only_mandatory_fields():
    # given
    expected_psp_reference = "psp:122:222"

    response_data = {
        "pspReference": expected_psp_reference,
        "event": {"type": TransactionEventType.CHARGE_SUCCESS.upper()},
    }

    # when
    parsed_data = parse_transaction_action_data(response_data)

    # then
    assert isinstance(parsed_data, TransactionRequestResponse)

    assert parsed_data.psp_reference == expected_psp_reference
    assert isinstance(parsed_data.event, TransactionRequestEventResponse)
    assert parsed_data.event.psp_reference == expected_psp_reference
    assert parsed_data.event.type == TransactionEventType.CHARGE_SUCCESS
    assert parsed_data.event.amount is None
    assert parsed_data.event.time == timezone.now()
    assert parsed_data.event.external_url == ""
    assert parsed_data.event.message == ""


@freeze_time("2018-05-31 12:00:01")
def test_parse_transaction_action_data_with_missin_psp_reference():
    # given
    response_data = {}

    # when
    parsed_data = parse_transaction_action_data(response_data)

    # then
    assert parsed_data is None


def test_parse_transaction_action_data_with_missing_mandatory_event_fields():
    # given
    expected_psp_reference = "psp:122:222"
    event_psp_reference = "psp:111:111"

    response_data = {
        "pspReference": expected_psp_reference,
        "event": {
            "pspReference": event_psp_reference,
        },
    }

    # when
    parsed_data = parse_transaction_action_data(response_data)

    # then
    assert parsed_data is None


def test_create_failed_transaction_event(transaction_item_created_by_app):
    # given
    cause = "Test failure"
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction_item_created_by_app.id,
    )

    # when
    failed_event = create_failed_transaction_event(request_event, cause=cause)

    # then
    assert failed_event.type == TransactionEventType.CHARGE_FAILURE
    assert failed_event.amount_value == request_event.amount_value
    assert failed_event.currency == request_event.currency
    assert failed_event.transaction_id == transaction_item_created_by_app.id


def test_create_transaction_event_from_request_and_webhook_response_with_psp_reference(
    transaction_item_created_by_app,
):
    # given
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction_item_created_by_app.id,
    )
    expected_psp_reference = "psp:122:222"
    response_data = {"pspReference": expected_psp_reference}

    # when
    create_transaction_event_from_request_and_webhook_response(
        request_event, response_data
    )

    # then
    request_event.refresh_from_db()
    assert request_event.psp_reference == expected_psp_reference
    assert TransactionEvent.objects.count() == 1


@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_from_request_and_webhook_response_part_event(
    transaction_item_created_by_app,
):
    # given
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction_item_created_by_app.id,
    )
    expected_psp_reference = "psp:122:222"
    response_data = {
        "pspReference": expected_psp_reference,
        "event": {
            "type": TransactionEventType.CHARGE_SUCCESS.upper(),
        },
    }

    # when
    event = create_transaction_event_from_request_and_webhook_response(
        request_event, response_data
    )

    # then
    assert TransactionEvent.objects.count() == 2
    request_event.refresh_from_db()
    assert request_event.psp_reference == expected_psp_reference
    assert event.psp_reference == expected_psp_reference
    assert event.amount_value == request_event.amount_value
    assert event.created_at == timezone.now()
    assert event.external_url == ""
    assert event.message == ""
    assert event.type == TransactionEventType.CHARGE_SUCCESS


@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_from_request_and_webhook_response_full_event(
    transaction_item_created_by_app,
):
    # given
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction_item_created_by_app.id,
    )

    event_amount = 12.00
    event_type = TransactionEventType.CHARGE_FAILURE
    event_time = "2022-11-18T13:25:58.169685+00:00"
    event_url = "http://localhost:3000/event/ref123"
    event_cause = "No cause"

    expected_psp_reference = "psp:122:222"

    response_data = {
        "pspReference": expected_psp_reference,
        "event": {
            "amount": event_amount,
            "type": event_type.upper(),
            "time": event_time,
            "externalUrl": event_url,
            "message": event_cause,
        },
    }

    # when
    event = create_transaction_event_from_request_and_webhook_response(
        request_event, response_data
    )

    # then
    assert TransactionEvent.objects.count() == 2
    request_event.refresh_from_db()
    assert request_event.psp_reference == expected_psp_reference
    assert event.psp_reference == expected_psp_reference
    assert event.amount_value == event_amount
    assert event.created_at == datetime.fromisoformat(event_time)
    assert event.external_url == event_url
    assert event.message == event_cause
    assert event.type == event_type


def test_create_transaction_event_from_request_and_webhook_response_incorrect_data(
    transaction_item_created_by_app,
):
    # given
    request_event = TransactionEvent.objects.create(
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=Decimal(11.00),
        currency="USD",
        transaction_id=transaction_item_created_by_app.id,
    )
    response_data = {"wrong-data": "psp:122:222"}

    # when
    failed_event = create_transaction_event_from_request_and_webhook_response(
        request_event, response_data
    )

    # then
    request_event.refresh_from_db()
    assert TransactionEvent.objects.count() == 2

    assert failed_event.type == TransactionEventType.CHARGE_FAILURE
    assert failed_event.amount_value == request_event.amount_value
    assert failed_event.currency == request_event.currency
    assert failed_event.transaction_id == transaction_item_created_by_app.id
