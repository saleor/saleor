import datetime
import logging
from decimal import Decimal
from unittest.mock import patch

import pytest
from freezegun import freeze_time

from ....order import OrderAuthorizeStatus
from ... import TransactionEventType
from ...models import TransactionEvent
from ...utils import (
    create_transaction_event_for_transaction_session,
    create_transaction_event_from_request_and_webhook_response,
)


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
    plugins_manager,
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
        create_transaction_event_for_transaction_session(
            request_event, app, plugins_manager, response_data
        )

    # then
    order.refresh_from_db()
    assert order_with_lines.authorize_status == OrderAuthorizeStatus.FULL
    assert not mock_order_fully_paid.called
    mock_order_updated.assert_called_once_with(order_with_lines, webhooks=set())


@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_from_request_updates_order_authorize(
    transaction_item_generator, app, order_with_lines, plugins_manager
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
    create_transaction_event_for_transaction_session(
        request_event, app, plugins_manager, response_data
    )

    # then
    order.refresh_from_db()
    assert order.total_authorized_amount == Decimal(event_amount)
    assert order.authorize_status == OrderAuthorizeStatus.PARTIAL


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
    expected_amount = Decimal(15)
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
def test_create_transaction_event_for_transaction_session_success_response_with_no_amount(
    response_result,
    transaction_amount_field_name,
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
):
    # given
    request_event_amount = Decimal(12)
    response = transaction_session_response.copy()
    response["result"] = response_result.upper()

    response["amount"] = None

    transaction = transaction_item_generator()
    request_event = TransactionEvent.objects.create(
        transaction=transaction,
        include_in_calculations=False,
        amount_value=request_event_amount,
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
    assert response_event.include_in_calculations
    assert response_event.amount_value == request_event_amount
    transaction.refresh_from_db()
    assert getattr(transaction, transaction_amount_field_name) == request_event_amount


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
    expected_amount = Decimal(0)
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
    expected_amount = Decimal(15)
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
    assert transaction.authorized_value == Decimal(0)
    assert transaction.charged_value == Decimal(0)
    assert transaction.authorize_pending_value == Decimal(0)
    assert transaction.charge_pending_value == Decimal(0)


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
def test_create_transaction_event_for_transaction_session_not_success_events_with_no_amount(
    response_result,
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
):
    # given
    expected_amount = Decimal(15)
    response = transaction_session_response.copy()
    response["result"] = response_result.upper()
    response["amount"] = None

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
    assert transaction.authorized_value == Decimal(0)
    assert transaction.charged_value == Decimal(0)
    assert transaction.authorize_pending_value == Decimal(0)
    assert transaction.charge_pending_value == Decimal(0)


@pytest.mark.parametrize(
    ("response_result", "message"),
    [
        (
            TransactionEventType.AUTHORIZATION_SUCCESS,
            "Missing value for field: pspReference.",
        ),
        (
            TransactionEventType.CHARGE_SUCCESS,
            "Missing value for field: pspReference.",
        ),
        (
            TransactionEventType.CHARGE_FAILURE,
            "Message related to the payment",
        ),
        (
            TransactionEventType.CHARGE_REQUEST,
            "Missing value for field: pspReference.",
        ),
        (
            TransactionEventType.AUTHORIZATION_REQUEST,
            "Missing value for field: pspReference.",
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
    expected_amount = Decimal(15)
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
    assert message in response_event.message
    transaction.refresh_from_db()
    assert transaction.authorized_value == Decimal(0)
    assert transaction.charged_value == Decimal(0)
    assert transaction.authorize_pending_value == Decimal(0)
    assert transaction.charge_pending_value == Decimal(0)


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
    expected_amount = Decimal(15)
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
    assert transaction.authorized_value == Decimal(0)
    assert transaction.charged_value == Decimal(0)
    assert transaction.authorize_pending_value == Decimal(0)
    assert transaction.charge_pending_value == Decimal(0)


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
    expected_amount = Decimal(15)
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
    expected_amount = Decimal(15)
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
    expected_amount = Decimal(15)
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


@pytest.mark.parametrize(
    "response_result",
    [
        TransactionEventType.AUTHORIZATION_REQUEST,
        TransactionEventType.CHARGE_REQUEST,
    ],
)
def test_create_transaction_event_for_transaction_session_request_events_as_response(
    response_result,
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
):
    # given
    expected_amount = Decimal(15)
    response = transaction_session_response.copy()
    response["result"] = response_result.upper()
    response["amount"] = expected_amount
    transaction = transaction_item_generator()
    request_event = TransactionEvent.objects.create(
        transaction=transaction, include_in_calculations=False
    )

    # when the response event is the `*_REQUEST` event
    response_event = create_transaction_event_for_transaction_session(
        request_event,
        webhook_app,
        manager=plugins_manager,
        transaction_webhook_response=response,
    )

    # then the response event should update the request event with the values
    # from the response
    assert response_event.id == request_event.id
    assert response_event.type == response_result
    assert response_event.include_in_calculations is True
    assert response_event.amount_value == expected_amount
    assert response_event.message == response["message"]
    assert response_event.external_url == response["externalUrl"]
    assert response_event.created_at == datetime.datetime.fromisoformat(
        response["time"]
    )
    assert response_event.psp_reference == response["pspReference"]


@freeze_time("2018-05-31 12:00:01")
def test_create_transaction_event_updates_transaction_modified_at(
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
    checkout,
):
    # given
    expected_amount = Decimal(15)
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
    expected_amount = Decimal(15)
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
    expected_amount = Decimal(15)
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
    expected_amount = Decimal(15)
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


def test_create_transaction_event_message_limit_exceeded(
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
    checkout,
    caplog,
):
    # given
    expected_amount = Decimal(15)
    message = "m" * 1000
    response = transaction_session_response.copy()
    response["amount"] = expected_amount
    response["message"] = message

    transaction = transaction_item_generator(checkout_id=checkout.pk)
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
    assert transaction.events.count() == 2
    event = transaction.events.last()
    assert event.message == message[:511] + "…"
    assert len(caplog.records) == 1
    assert caplog.records[0].message == (
        "Value for field: message in response of transaction action webhook "
        "exceeds the character field limit. Message has been truncated."
    )
    assert caplog.records[0].levelno == logging.WARNING


@pytest.mark.parametrize(
    ("input_message", "expected_message"),
    [("m" * 512, "m" * 512), (None, ""), ("", ""), (5, "5"), ("你好世界", "你好世界")],
)
def test_create_transaction_event_with_message(
    input_message,
    expected_message,
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
    checkout,
):
    # given
    expected_amount = Decimal(15)
    response = transaction_session_response.copy()
    response["amount"] = expected_amount
    response["message"] = input_message

    transaction = transaction_item_generator(checkout_id=checkout.pk)
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
    assert transaction.events.count() == 2
    event = transaction.events.last()
    assert event.message == expected_message


def test_create_transaction_event_with_invalid_message(
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
    checkout,
    caplog,
):
    # given
    class NonParsableObject:
        def __str__(self):
            raise "こんにちは".encode("ascii")

    expected_amount = Decimal(15)
    response = transaction_session_response.copy()
    response["amount"] = expected_amount
    response["message"] = NonParsableObject()

    transaction = transaction_item_generator(checkout_id=checkout.pk)
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
    assert transaction.events.count() == 2
    event = transaction.events.last()
    assert event.message == ""
    assert (
        "Incorrect value for field: message in response of transaction action webhook."
    ) in (record.message for record in caplog.records)


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
def test_create_transaction_event_for_transaction_session_twice_auth(
    transaction_item_generator,
    app,
    plugins_manager,
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
    failed_event = create_transaction_event_for_transaction_session(
        request_event, app, plugins_manager, response_data
    )

    # then
    assert TransactionEvent.objects.count() == 3
    assert failed_event
    assert failed_event.psp_reference == request_event.psp_reference
    assert failed_event.type == TransactionEventType.AUTHORIZATION_FAILURE


@pytest.mark.parametrize(
    "response_result",
    [
        TransactionEventType.AUTHORIZATION_REQUEST,
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.CHARGE_REQUEST,
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.AUTHORIZATION_ACTION_REQUIRED,
        TransactionEventType.CHARGE_ACTION_REQUIRED,
        TransactionEventType.AUTHORIZATION_FAILURE,
        TransactionEventType.CHARGE_FAILURE,
    ],
)
@pytest.mark.parametrize(
    "payment_method_details",
    [
        {
            "type": "CARD",
            "name": "Test Card",
            "brand": "Brand",
            "firstDigits": "1234",
            "lastDigits": "5678",
            "expMonth": 12,
            "expYear": 2025,
        },
        {
            "type": "CARD",
            "name": "Test Card",
        },
        {
            "type": "CARD",
            "name": "Test Card",
            "brand": "Brand",
            "lastDigits": "5678",
        },
        {
            "type": "OTHER",
            "name": "Test Other",
        },
    ],
)
def test_create_transaction_event_for_transaction_session_sets_payment_method_details(
    payment_method_details,
    response_result,
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
):
    # given
    expected_amount = Decimal(15)
    response = transaction_session_response.copy()
    response["result"] = response_result.upper()
    response["amount"] = expected_amount
    response["paymentMethodDetails"] = payment_method_details

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
    assert response_event
    transaction.refresh_from_db()
    assert transaction.payment_method_name == payment_method_details["name"]
    assert transaction.payment_method_type == payment_method_details["type"].lower()
    assert transaction.cc_brand == payment_method_details.get("brand")
    assert transaction.cc_first_digits == payment_method_details.get("firstDigits")
    assert transaction.cc_last_digits == payment_method_details.get("lastDigits")
    assert transaction.cc_exp_month == payment_method_details.get("expMonth")
    assert transaction.cc_exp_year == payment_method_details.get("expYear")


@pytest.mark.parametrize(
    "response_result",
    [
        TransactionEventType.AUTHORIZATION_REQUEST,
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.CHARGE_REQUEST,
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.AUTHORIZATION_ACTION_REQUIRED,
        TransactionEventType.CHARGE_ACTION_REQUIRED,
        TransactionEventType.AUTHORIZATION_FAILURE,
        TransactionEventType.CHARGE_FAILURE,
    ],
)
@pytest.mark.parametrize(
    "payment_method_details",
    [
        # unknown type
        {
            "type": "WRONG-TYPE",
            "name": "Test Card",
        },
        # Missing name
        {
            "type": "CARD",
        },
        # Missing type
        {
            "name": "Test Card",
        },
    ],
)
def test_create_transaction_event_for_transaction_session_invalid_payment_method_details(
    payment_method_details,
    response_result,
    transaction_item_generator,
    transaction_session_response,
    webhook_app,
    plugins_manager,
):
    # given
    expected_amount = Decimal(15)
    response = transaction_session_response.copy()
    response["result"] = response_result.upper()
    response["amount"] = expected_amount
    response["paymentMethodDetails"] = payment_method_details

    transaction = transaction_item_generator()
    request_event = TransactionEvent.objects.create(
        transaction=transaction,
        include_in_calculations=False,
        type=TransactionEventType.AUTHORIZATION_REQUEST,
    )
    # when
    response_event = create_transaction_event_for_transaction_session(
        request_event,
        webhook_app,
        manager=plugins_manager,
        transaction_webhook_response=response,
    )

    # then
    assert response_event
    assert response_event.type == TransactionEventType.AUTHORIZATION_FAILURE
    assert "paymentMethodDetails" in response_event.message

    transaction.refresh_from_db()
    assert not transaction.payment_method_name
    assert not transaction.payment_method_type
    assert not transaction.cc_brand
    assert not transaction.cc_first_digits
    assert not transaction.cc_last_digits
    assert not transaction.cc_exp_month
    assert not transaction.cc_exp_year
