from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.utils import timezone
from freezegun import freeze_time
from pydantic import ValidationError

from ....payment import TransactionAction, TransactionEventType
from ...response_schemas.transaction import (
    TransactionCancelRequestedResponse,
    TransactionChargeRequestedResponse,
    TransactionRefundRequestedResponse,
    TransactionResponse,
    TransactionSessionResponse,
)


def test_transaction_response_valid_full_data():
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "time": "2023-01-01T12:00:00+00:00",
        "externalUrl": "https://example.com/",
        "message": "Transaction completed successfully.",
        "actions": [TransactionAction.CHARGE.upper(), TransactionAction.REFUND.upper()],
        "result": TransactionEventType.CHARGE_SUCCESS.upper(),
    }

    # when
    transaction = TransactionResponse.model_validate(data)

    # then
    assert transaction.psp_reference == data["pspReference"]
    assert transaction.amount == data["amount"]
    assert transaction.time.isoformat() == data["time"]
    assert str(transaction.external_url) == data["externalUrl"]
    assert transaction.message == data["message"]
    assert transaction.actions == [action.lower() for action in data.get("actions")]
    assert transaction.result == data["result"].lower()


@pytest.mark.parametrize(
    "data",
    [
        # Only required fields with values
        {
            "pspReference": None,
            "amount": Decimal("100.50"),
            "time": None,
            "externalUrl": None,
            "message": None,
            "actions": None,
            "result": TransactionEventType.CHARGE_ACTION_REQUIRED.upper(),
        },
        # Only required fields with values
        {
            "amount": Decimal("100.50"),
            "result": TransactionEventType.CHARGE_ACTION_REQUIRED.upper(),
        },
    ],
)
@freeze_time("2023-01-01T12:00:00+00:00")
def test_transaction_response_valid_only_required_fields(data):
    # when
    transaction = TransactionResponse.model_validate(data)

    # then
    assert transaction.psp_reference is None
    assert transaction.amount == data["amount"]
    assert transaction.time.isoformat() == timezone.now().isoformat()
    assert str(transaction.external_url) == ""
    assert transaction.message == ""
    assert transaction.actions is None
    assert transaction.result == data["result"].lower()


@pytest.mark.parametrize(
    "amount",
    [Decimal("100.50"), 100.50, 100, "100.50"],
)
def test_transaction_response_with_various_amount_types(amount):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": amount,
        "result": TransactionEventType.CHARGE_SUCCESS.upper(),
    }

    # when
    transaction = TransactionResponse.model_validate(data)

    # then
    assert transaction.amount == Decimal(str(amount))


@pytest.mark.parametrize(
    ("time", "time_parser"),
    [
        # ISO 8601 format with timezone
        ("2023-01-01T12:00:00+00:00", datetime.fromisoformat),
        # ISO 8601 format without timezone
        ("2023-01-01T12:00:00", datetime.fromisoformat),
        # ISO 8601 format with milliseconds
        ("2023-01-01T12:00:00.123+00:00", datetime.fromisoformat),
        # ISO 8601 format with week-based date
        ("2023-W01-1T12:00:00", datetime.fromisoformat),
        # Time as integer
        (1672531200, datetime.fromtimestamp),
        # No time provided (should use current time)
        (None, None),
    ],
)
@freeze_time("2023-01-01T12:00:00+00:00")
def test_transaction_response_time_valid(time, time_parser):
    # given
    data = {
        "pspReference": "123",
        "amount": Decimal("100.00"),
        "result": TransactionEventType.CHARGE_SUCCESS.upper(),
        "time": time,
    }

    # when
    transaction = TransactionResponse.model_validate(data)

    # then
    time = data.get("time")
    parsed_time = time_parser(time) if time else timezone.now()
    assert transaction.time == parsed_time.replace(tzinfo=UTC)


@pytest.mark.parametrize(
    ("actions", "expected_actions"),
    [
        # Valid actions
        (
            [
                TransactionAction.CHARGE.upper(),
                TransactionAction.REFUND.upper(),
                TransactionAction.CANCEL.upper(),
            ],
            [
                TransactionAction.CHARGE,
                TransactionAction.REFUND,
                TransactionAction.CANCEL,
            ],
        ),
        # Just one action
        (
            [TransactionAction.CANCEL.upper()],
            [TransactionAction.CANCEL],
        ),
        # Invalid actions (should skip invalid ones)
        (
            ["INVALID", TransactionAction.REFUND.upper()],
            [TransactionAction.REFUND],
        ),
        # Empty actions list
        (
            [],
            [],
        ),
        # None actions
        (
            None,
            None,
        ),
    ],
)
def test_transaction_response_actions_validation(actions, expected_actions):
    # given
    data = {
        "pspReference": "123",
        "amount": Decimal("100.00"),
        "result": TransactionEventType.CHARGE_SUCCESS.upper(),
        "actions": actions,
    }

    # when
    transaction = TransactionResponse.model_validate(data)

    # then
    assert transaction.actions == expected_actions


@pytest.mark.parametrize(
    "data",
    [
        # Time as a string value
        {
            "pspReference": "123",
            "amount": Decimal("100.00"),
            "result": TransactionEventType.CHARGE_SUCCESS.upper(),
            "time": "invalid-time",
        },
        # Invalid external URL
        {
            "amount": "100.50",
            "result": TransactionEventType.CHARGE_SUCCESS.upper(),
            "externalUrl": "invalid-url",
        },
    ],
)
def test_transaction_response_invalid(data):
    # when
    with pytest.raises(ValidationError) as error:
        TransactionResponse.model_validate(data)

    # then
    assert len(error.value.errors()) == 1


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.CANCEL_SUCCESS,
        TransactionEventType.REFUND_SUCCESS,
        TransactionEventType.CHARGE_BACK,
        TransactionEventType.REFUND_REVERSE,
    ],
)
def test_transaction_response_time_missing_psp_reference(result):
    # given
    data = {
        "amount": Decimal("100.00"),
        "result": result.upper(),
    }

    # when/then
    with pytest.raises(ValidationError) as error:
        TransactionResponse.model_validate(data)

    assert len(error.value.errors()) == 1


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.CHARGE_FAILURE,
    ],
)
def test_transaction_charge_requested_response_valid(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "time": "2023-01-01T12:00:00+00:00",
        "externalUrl": "https://example.com/",
        "message": "Transaction completed successfully.",
        "actions": [TransactionAction.CHARGE.upper(), TransactionAction.REFUND.upper()],
        "result": result.upper(),
    }

    # when
    transaction = TransactionChargeRequestedResponse.model_validate(data)

    # then
    assert transaction.result == result


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.CANCEL_FAILURE,
        TransactionEventType.REFUND_FAILURE,
        TransactionEventType.CANCEL_SUCCESS,
        TransactionEventType.REFUND_SUCCESS,
    ],
)
def test_transaction_charge_requested_response_invalid(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "time": "2023-01-01T12:00:00+00:00",
        "externalUrl": "https://example.com/",
        "message": "Transaction completed successfully.",
        "actions": [TransactionAction.CHARGE.upper(), TransactionAction.REFUND.upper()],
        "result": result.upper(),
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionChargeRequestedResponse.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.CANCEL_SUCCESS,
        TransactionEventType.CANCEL_FAILURE,
    ],
)
def test_transaction_cancel_requested_response_valid(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "time": "2023-01-01T12:00:00+00:00",
        "externalUrl": "https://example.com/",
        "message": "Transaction completed successfully.",
        "actions": [TransactionAction.CHARGE.upper(), TransactionAction.REFUND.upper()],
        "result": result.upper(),
    }

    # when
    transaction = TransactionCancelRequestedResponse.model_validate(data)

    # then
    assert transaction.result == result


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.CHARGE_FAILURE,
        TransactionEventType.REFUND_FAILURE,
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.REFUND_SUCCESS,
    ],
)
def test_transaction_cancel_requested_response_invalid(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "time": "2023-01-01T12:00:00+00:00",
        "externalUrl": "https://example.com/",
        "message": "Transaction completed successfully.",
        "actions": [TransactionAction.CHARGE.upper(), TransactionAction.REFUND.upper()],
        "result": result.upper(),
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionCancelRequestedResponse.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.REFUND_SUCCESS,
        TransactionEventType.REFUND_FAILURE,
    ],
)
def test_transaction_refund_requested_response_valid(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "time": "2023-01-01T12:00:00+00:00",
        "externalUrl": "https://example.com/",
        "message": "Transaction completed successfully.",
        "actions": [TransactionAction.CHARGE.upper(), TransactionAction.REFUND.upper()],
        "result": result.upper(),
    }

    # when
    transaction = TransactionRefundRequestedResponse.model_validate(data)

    # then
    assert transaction.result == result


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.CHARGE_FAILURE,
        TransactionEventType.CANCEL_FAILURE,
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.CANCEL_SUCCESS,
    ],
)
def test_transaction_refund_requested_response_invalid(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "time": "2023-01-01T12:00:00+00:00",
        "externalUrl": "https://example.com/",
        "message": "Transaction completed successfully.",
        "actions": [TransactionAction.CHARGE.upper(), TransactionAction.REFUND.upper()],
        "result": result.upper(),
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionRefundRequestedResponse.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.AUTHORIZATION_FAILURE,
        TransactionEventType.AUTHORIZATION_ACTION_REQUIRED,
        TransactionEventType.AUTHORIZATION_REQUEST,
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.CHARGE_FAILURE,
        TransactionEventType.CHARGE_ACTION_REQUIRED,
        TransactionEventType.CHARGE_REQUEST,
    ],
)
def test_transaction_session_response_valid_result(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "time": "2023-01-01T12:00:00+00:00",
        "externalUrl": "https://example.com/",
        "message": "Transaction completed successfully.",
        "actions": [TransactionAction.CHARGE.upper(), TransactionAction.REFUND.upper()],
        "result": result.upper(),
        "data": "test-data",
    }

    # when
    transaction = TransactionSessionResponse.model_validate(data)

    # then
    assert transaction.result == result


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.REFUND_FAILURE,
        TransactionEventType.CANCEL_FAILURE,
        TransactionEventType.REFUND_SUCCESS,
        TransactionEventType.CANCEL_SUCCESS,
    ],
)
def test_transaction_session_response_invalid_result(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "time": "2023-01-01T12:00:00+00:00",
        "externalUrl": "https://example.com/",
        "message": "Transaction completed successfully.",
        "actions": [TransactionAction.CHARGE.upper(), TransactionAction.REFUND.upper()],
        "result": result.upper(),
        "data": "data",
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionSessionResponse.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1


@pytest.mark.parametrize(
    "data",
    [
        # Valid data
        {"key": "value", "another_key": "another_value"},
        # Empty data
        {},
        # Data with special characters
        {"key": "!@#$%^&*()_+"},
        # Data with nested structure
        {"nested": {"key": "value"}},
        # Data with list
        {"list": ["item1", "item2", "item3"]},
        # Data as None
        None,
        # Data as string
        "string_data",
        # Data as integer
        123,
    ],
)
def test_transaction_session_response_valid_data(data):
    # given
    input_data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "time": "2023-01-01T12:00:00+00:00",
        "externalUrl": "https://example.com/",
        "message": "Transaction completed successfully.",
        "actions": [TransactionAction.CHARGE.upper(), TransactionAction.REFUND.upper()],
        "result": TransactionEventType.AUTHORIZATION_SUCCESS.upper(),
        "data": data,
    }

    # when
    transaction = TransactionSessionResponse.model_validate(input_data)

    # then
    assert transaction.data == data
