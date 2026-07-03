import datetime
from decimal import Decimal

import pytest
from freezegun import freeze_time

from ... import TransactionEventType
from ...interface import TransactionRequestEventResponse, TransactionSessionResponse
from ...utils import (
    parse_transaction_action_data_for_session_webhook,
)


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
def test_parse_transaction_action_data_for_session_webhook_with_provided_time(
    event_time, expected_datetime
):
    # given
    request_event_amount = Decimal(10.00)
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
    parsed_data, error_msg = parse_transaction_action_data_for_session_webhook(
        response_data, request_event_amount
    )
    # then
    assert isinstance(parsed_data, TransactionSessionResponse)
    assert parsed_data.event.time == expected_datetime


def test_parse_transaction_action_data_for_session_webhook_with_event_all_fields_provided():
    # given
    request_event_amount = Decimal(10.00)

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
    parsed_data, error_msg = parse_transaction_action_data_for_session_webhook(
        response_data, request_event_amount
    )
    # then
    assert isinstance(parsed_data, TransactionSessionResponse)
    assert error_msg is None

    assert parsed_data.psp_reference == expected_psp_reference
    assert isinstance(parsed_data.event, TransactionRequestEventResponse)
    assert parsed_data.event.psp_reference == expected_psp_reference
    assert parsed_data.event.amount == event_amount
    assert parsed_data.event.time == datetime.datetime.fromisoformat(event_time)
    assert parsed_data.event.external_url == event_url
    assert parsed_data.event.message == event_cause
    assert parsed_data.event.type == event_type


def test_parse_transaction_action_data_for_session_webhook_with_incorrect_result():
    # given
    request_event_amount = Decimal(10.00)
    expected_psp_reference = "psp:122:222"
    event_amount = 12.00
    event_type = TransactionEventType.REFUND_SUCCESS
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
    parsed_data, error_msg = parse_transaction_action_data_for_session_webhook(
        response_data, request_event_amount
    )

    # then
    assert parsed_data is None
    assert (
        f"Missing or invalid value for `result`: {response_data['result']}" in error_msg
    )


@freeze_time("2018-05-31 12:00:01")
def test_parse_transaction_action_data_for_session_webhook_with_event_only_mandatory_fields():
    # given
    expected_psp_reference = "psp:122:222"
    expected_amount = Decimal("10.00")
    response_data = {
        "pspReference": expected_psp_reference,
        "result": TransactionEventType.CHARGE_SUCCESS.upper(),
    }

    # when
    parsed_data, _ = parse_transaction_action_data_for_session_webhook(
        response_data, expected_amount
    )

    # then
    assert isinstance(parsed_data, TransactionSessionResponse)

    assert parsed_data.psp_reference == expected_psp_reference
    assert isinstance(parsed_data.event, TransactionRequestEventResponse)
    assert parsed_data.event.psp_reference == expected_psp_reference
    assert parsed_data.event.type == TransactionEventType.CHARGE_SUCCESS
    assert parsed_data.event.amount == expected_amount
    assert parsed_data.event.time == datetime.datetime.now(tz=datetime.UTC)
    assert parsed_data.event.external_url == ""
    assert parsed_data.event.message == ""


def test_parse_transaction_action_data_for_session_webhook_use_provided_amount_when_event_amount_is_missing():
    # given
    request_event_amount = Decimal(10.00)
    response_data = {
        "pspReference": "123",
        "result": TransactionEventType.CHARGE_SUCCESS.upper(),
    }

    # when
    parsed_data, _ = parse_transaction_action_data_for_session_webhook(
        response_data, request_event_amount
    )

    # then
    assert isinstance(parsed_data, TransactionSessionResponse)
    assert parsed_data.event.amount == request_event_amount


def test_parse_transaction_action_data_for_session_webhook_skips_input_amount_when_event_has_amount():
    # given
    request_event_amount = Decimal(10.00)
    expected_amount = Decimal(12.00)

    assert request_event_amount != expected_amount
    response_data = {
        "pspReference": "123",
        "result": TransactionEventType.CHARGE_SUCCESS.upper(),
        "amount": expected_amount,
    }

    # when
    parsed_data, _ = parse_transaction_action_data_for_session_webhook(
        response_data, request_event_amount
    )

    # then
    assert isinstance(parsed_data, TransactionSessionResponse)
    assert parsed_data.event.amount == expected_amount


@freeze_time("2018-05-31 12:00:01")
def test_parse_transaction_action_data_for_session_webhook_with_empty_response():
    # given
    response_data = {}

    # when
    parsed_data, _ = parse_transaction_action_data_for_session_webhook(
        response_data, Decimal(10.00)
    )

    # then
    assert parsed_data is None


def test_parse_transaction_action_data_for_session_webhook_with_missing_optional_psp_reference():
    # given
    response_data = {
        "result": TransactionEventType.CHARGE_FAILURE.upper(),
    }

    # when
    parsed_data, _ = parse_transaction_action_data_for_session_webhook(
        response_data, Decimal("10.00")
    )

    # then
    assert parsed_data


def test_parse_transaction_action_data_with_missing_mandatory_event_fields():
    # given
    expected_psp_reference = "psp:122:222"

    response_data = {
        "pspReference": expected_psp_reference,
    }

    # when
    parsed_data, _ = parse_transaction_action_data_for_session_webhook(
        response_data, Decimal("10.00")
    )

    # then
    assert parsed_data is None
