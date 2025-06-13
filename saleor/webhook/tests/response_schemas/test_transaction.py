import math
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.utils import timezone
from freezegun import freeze_time
from pydantic import ValidationError

from ....payment import TransactionAction, TransactionEventType
from ...response_schemas.transaction import (
    PaymentGatewayInitializeSessionSchema,
    TransactionBaseSchema,
    TransactionCancelationRequestedAsyncSchema,
    TransactionCancelationRequestedSyncFailureSchema,
    TransactionCancelationRequestedSyncSuccessSchema,
    TransactionChargeRequestedAsyncSchema,
    TransactionChargeRequestedSyncFailureSchema,
    TransactionChargeRequestedSyncSuccessSchema,
    TransactionRefundRequestedAsyncSchema,
    TransactionRefundRequestedSyncFailureSchema,
    TransactionRefundRequestedSyncSuccessSchema,
    TransactionSessionActionRequiredSchema,
    TransactionSessionBaseSchema,
    TransactionSessionFailureSchema,
    TransactionSessionSuccessSchema,
)


def test_transaction_schema_valid_full_data():
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
    transaction = TransactionBaseSchema.model_validate(data)

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
def test_transaction_schema_valid_only_required_fields(data):
    # when
    transaction = TransactionBaseSchema.model_validate(data)

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
def test_transaction_schema_with_various_amount_types(amount):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": amount,
        "result": TransactionEventType.CHARGE_SUCCESS.upper(),
    }

    # when
    transaction = TransactionBaseSchema.model_validate(data)

    # then
    assert transaction.amount == Decimal(str(amount))


@pytest.mark.parametrize(
    ("time", "expected_datetime"),
    [
        # ISO 8601 format with timezone
        ("2023-05-05T12:00:00+02:00", datetime(2023, 5, 5, 10, 0, 0, tzinfo=UTC)),
        # ISO 8601 format without timezone
        ("2023-02-04T10:15:22", datetime(2023, 2, 4, 10, 15, 22, tzinfo=UTC)),
        # ISO 8601 format with milliseconds
        (
            "2023-01-01T12:00:00.123+00:00",
            datetime(2023, 1, 1, 12, 0, 0, 123000, tzinfo=UTC),
        ),
        # ISO 8601 format with week-based date
        ("2023-W02-1T12:00:00", datetime(2023, 1, 9, 12, 0, tzinfo=UTC)),
        # Time as integer
        (1672531400, datetime(2023, 1, 1, 0, 3, 20, tzinfo=UTC)),
        # No time provided (should use current time)
        (None, datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)),
    ],
)
@freeze_time("2023-01-01T12:00:00+00:00")
def test_transaction_schema_time_valid(time, expected_datetime):
    # given
    data = {
        "pspReference": "123",
        "amount": Decimal("100.00"),
        "result": TransactionEventType.CHARGE_SUCCESS.upper(),
        "time": time,
    }

    # when
    transaction = TransactionBaseSchema.model_validate(data)

    # then
    assert transaction.time == expected_datetime


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
def test_transaction_schema_actions_validation(actions, expected_actions):
    # given
    data = {
        "pspReference": "123",
        "amount": Decimal("100.00"),
        "result": TransactionEventType.CHARGE_SUCCESS.upper(),
        "actions": actions,
    }

    # when
    transaction = TransactionBaseSchema.model_validate(data)

    # then
    assert transaction.actions == expected_actions


@pytest.mark.parametrize(
    ("data", "invalid_field"),
    [
        # Time as a string value
        (
            {
                "pspReference": "123",
                "amount": Decimal("100.00"),
                "result": TransactionEventType.CHARGE_SUCCESS.upper(),
                "time": "invalid-time",
            },
            "time",
        ),
        # Invalid external URL
        (
            {
                "amount": "100.50",
                "result": TransactionEventType.CHARGE_SUCCESS.upper(),
                "externalUrl": "invalid-url",
            },
            "externalUrl",
        ),
        # Infinitive amount
        (
            {
                "pspReference": "123",
                "amount": math.inf,
                "result": TransactionEventType.CHARGE_SUCCESS.upper(),
            },
            "amount",
        ),
    ],
)
def test_transaction_schema_invalid(data, invalid_field):
    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionBaseSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"] == (invalid_field,)


def test_transaction_charge_requested_sync_success_schema_valid():
    # given
    result = TransactionEventType.CHARGE_SUCCESS
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
    transaction = TransactionChargeRequestedSyncSuccessSchema.model_validate(data)

    # then
    assert transaction.result == result


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.CANCEL_SUCCESS,
        TransactionEventType.REFUND_SUCCESS,
        TransactionEventType.CANCEL_FAILURE,
        TransactionEventType.REFUND_FAILURE,
    ],
)
def test_transaction_charge_requested_sync_success_schema_invalid(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionChargeRequestedSyncSuccessSchema.model_validate(data)
    assert len(exc_info.value.errors()) == 1

    # then
    assert exc_info.value.errors()[0]["loc"] == ("result",)


def test_transaction_charge_requested_sync_failure_schema_valid():
    # given
    result = TransactionEventType.CHARGE_FAILURE
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "time": "2023-01-01T12:00:00+00:00",
        "externalUrl": "https://example.com/",
        "message": "Transaction failed.",
        "actions": [TransactionAction.CHARGE.upper(), TransactionAction.REFUND.upper()],
        "result": result.upper(),
    }

    # when
    transaction = TransactionChargeRequestedSyncFailureSchema.model_validate(data)

    # then
    assert transaction.result == result


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.CANCEL_SUCCESS,
        TransactionEventType.REFUND_SUCCESS,
        TransactionEventType.CANCEL_FAILURE,
        TransactionEventType.REFUND_FAILURE,
    ],
)
def test_transaction_charge_requested_sync_failure_schema_invalid(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionChargeRequestedSyncFailureSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"] == ("result",)


def test_transaction_charge_requested_async_schema_valid():
    # given
    data = {
        "pspReference": "psp-async-123",
        "actions": [TransactionAction.CHARGE.upper()],
    }

    # when
    transaction = TransactionChargeRequestedAsyncSchema.model_validate(data)

    # then
    assert transaction.psp_reference == "psp-async-123"


def test_transaction_charge_requested_async_schema_invalid():
    # given
    data = {
        "pspReference": 123,
        "actions": [TransactionAction.CHARGE.upper()],
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionChargeRequestedAsyncSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"] == ("pspReference",)


def test_transaction_cancel_requested_sync_success_schema_valid():
    # given
    result = TransactionEventType.CANCEL_SUCCESS
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "time": "2023-01-01T12:00:00+00:00",
        "externalUrl": "https://example.com/",
        "message": "Transaction cancelled successfully.",
        "actions": [TransactionAction.CANCEL.upper(), TransactionAction.REFUND.upper()],
        "result": result.upper(),
    }

    # when
    transaction = TransactionCancelationRequestedSyncSuccessSchema.model_validate(data)

    # then
    assert transaction.result == result


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.REFUND_SUCCESS,
        TransactionEventType.CHARGE_FAILURE,
        TransactionEventType.REFUND_FAILURE,
    ],
)
def test_transaction_cancel_requested_sync_success_schema_invalid(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionCancelationRequestedSyncSuccessSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"] == ("result",)


def test_transaction_cancel_requested_sync_failure_schema_valid():
    # given
    result = TransactionEventType.CANCEL_FAILURE
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "time": "2023-01-01T12:00:00+00:00",
        "externalUrl": "https://example.com/",
        "message": "Transaction cancel failed.",
        "actions": [TransactionAction.CANCEL.upper(), TransactionAction.REFUND.upper()],
        "result": result.upper(),
    }

    # when
    transaction = TransactionCancelationRequestedSyncFailureSchema.model_validate(data)

    # then
    assert transaction.result == result


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.REFUND_SUCCESS,
        TransactionEventType.CHARGE_FAILURE,
        TransactionEventType.REFUND_FAILURE,
    ],
)
def test_transaction_cancel_requested_sync_failure_schema_invalid(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionCancelationRequestedSyncFailureSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"] == ("result",)


def test_transaction_cancel_requested_async_schema_valid():
    # given
    data = {
        "pspReference": "psp-async-123",
        "actions": [TransactionAction.CANCEL.upper()],
    }

    # when
    transaction = TransactionCancelationRequestedAsyncSchema.model_validate(data)

    # then
    assert transaction.psp_reference == "psp-async-123"


def test_transaction_cancel_requested_async_schema_invalid():
    # given
    data = {
        "pspReference": 123,
        "actions": [TransactionAction.CANCEL.upper()],
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionCancelationRequestedAsyncSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"] == ("pspReference",)


def test_transaction_refund_requested_sync_success_schema_valid():
    # given
    result = TransactionEventType.REFUND_SUCCESS
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "time": "2023-01-01T12:00:00+00:00",
        "externalUrl": "https://example.com/",
        "message": "Transaction refunded successfully.",
        "actions": [TransactionAction.REFUND.upper(), TransactionAction.CHARGE.upper()],
        "result": result.upper(),
    }

    # when
    transaction = TransactionRefundRequestedSyncSuccessSchema.model_validate(data)

    # then
    assert transaction.result == result


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.CANCEL_SUCCESS,
        TransactionEventType.CHARGE_FAILURE,
        TransactionEventType.CANCEL_FAILURE,
    ],
)
def test_transaction_refund_requested_sync_success_schema_invalid(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionRefundRequestedSyncSuccessSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"] == ("result",)


def test_transaction_refund_requested_sync_failure_schema_valid():
    # given
    result = TransactionEventType.REFUND_FAILURE
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "time": "2023-01-01T12:00:00+00:00",
        "externalUrl": "https://example.com/",
        "message": "Transaction refund failed.",
        "actions": [TransactionAction.REFUND.upper(), TransactionAction.CHARGE.upper()],
        "result": result.upper(),
    }

    # when
    transaction = TransactionRefundRequestedSyncFailureSchema.model_validate(data)

    # then
    assert transaction.result == result


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.CANCEL_SUCCESS,
        TransactionEventType.CHARGE_FAILURE,
        TransactionEventType.CANCEL_FAILURE,
    ],
)
def test_transaction_refund_requested_sync_failure_schema_invalid(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionRefundRequestedSyncFailureSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"] == ("result",)


def test_transaction_refund_requested_async_schema_valid():
    # given
    data = {
        "pspReference": "psp-async-123",
        "actions": [TransactionAction.REFUND.upper()],
    }

    # when
    transaction = TransactionRefundRequestedAsyncSchema.model_validate(data)

    # then
    assert transaction.psp_reference == "psp-async-123"


def test_transaction_refund_requested_async_schema_invalid():
    # given
    data = {
        "pspReference": 123,
        "actions": [TransactionAction.REFUND.upper()],
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionRefundRequestedAsyncSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"] == ("pspReference",)


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_ACTION_REQUIRED,
        TransactionEventType.CHARGE_ACTION_REQUIRED,
    ],
)
def test_transaction_session_action_required_schema_valid_result(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
        "data": "test-data",
    }

    # when
    transaction = TransactionSessionActionRequiredSchema.model_validate(data)

    # then
    assert transaction.result == result


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_ACTION_REQUIRED,
        TransactionEventType.CHARGE_ACTION_REQUIRED,
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
        {
            "type": "CARD",
            "name": "Test Card",
            "brand": None,
            "firstDigits": None,
            "lastDigits": None,
            "expMonth": None,
            "expYear": None,
        },
    ],
)
def test_transaction_session_action_required_schema_valid_payment_method_details(
    payment_method_details, result
):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
        "data": "test-data",
        "paymentMethodDetails": payment_method_details,
    }

    # when
    parsed_transaction = TransactionSessionActionRequiredSchema.model_validate(data)

    # then
    assert parsed_transaction.result == result
    assert parsed_transaction.payment_method_details
    parsed_payment_method_details = parsed_transaction.payment_method_details

    assert parsed_payment_method_details.type == payment_method_details["type"].lower()
    assert parsed_payment_method_details.name == payment_method_details["name"]
    assert getattr(
        parsed_payment_method_details, "brand", None
    ) == payment_method_details.get("brand")
    assert getattr(
        parsed_payment_method_details, "first_digits", None
    ) == payment_method_details.get("firstDigits")
    assert getattr(
        parsed_payment_method_details, "last_digits", None
    ) == payment_method_details.get("lastDigits")
    assert getattr(
        parsed_payment_method_details, "exp_month", None
    ) == payment_method_details.get("expMonth")
    assert getattr(
        parsed_payment_method_details, "exp_year", None
    ) == payment_method_details.get("expYear")


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_ACTION_REQUIRED,
        TransactionEventType.CHARGE_ACTION_REQUIRED,
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
def test_transaction_session_action_required_schema_invalid_payment_method_details(
    payment_method_details, result
):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
        "data": "test-data",
        "paymentMethodDetails": payment_method_details,
    }

    # when & then
    with pytest.raises(ValidationError):
        TransactionSessionActionRequiredSchema.model_validate(data)


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.AUTHORIZATION_FAILURE,
        TransactionEventType.CHARGE_FAILURE,
        TransactionEventType.AUTHORIZATION_REQUEST,
        TransactionEventType.CHARGE_REQUEST,
        TransactionEventType.REFUND_SUCCESS,
        TransactionEventType.CANCEL_SUCCESS,
    ],
)
def test_transaction_session_action_required_schema_invalid_result(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
        "data": "test-data",
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionSessionActionRequiredSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"] == ("result",)


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.AUTHORIZATION_REQUEST,
        TransactionEventType.CHARGE_REQUEST,
    ],
)
def test_transaction_session_success_schema_valid_result(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
        "data": "test-data",
    }

    # when
    transaction = TransactionSessionSuccessSchema.model_validate(data)

    # then
    assert transaction.result == result


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.AUTHORIZATION_REQUEST,
        TransactionEventType.CHARGE_REQUEST,
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
        {
            "type": "CARD",
            "name": "Test Card",
            "brand": None,
            "firstDigits": None,
            "lastDigits": None,
            "expMonth": None,
            "expYear": None,
        },
    ],
)
def test_transaction_session_success_schema_valid_payment_method_details(
    payment_method_details, result
):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
        "data": "test-data",
        "paymentMethodDetails": payment_method_details,
    }

    # when
    parsed_transaction = TransactionSessionSuccessSchema.model_validate(data)

    # then
    assert parsed_transaction.result == result
    assert parsed_transaction.payment_method_details
    parsed_payment_method_details = parsed_transaction.payment_method_details

    assert parsed_payment_method_details.type == payment_method_details["type"].lower()
    assert parsed_payment_method_details.name == payment_method_details["name"]
    assert getattr(
        parsed_payment_method_details, "brand", None
    ) == payment_method_details.get("brand")
    assert getattr(
        parsed_payment_method_details, "first_digits", None
    ) == payment_method_details.get("firstDigits")
    assert getattr(
        parsed_payment_method_details, "last_digits", None
    ) == payment_method_details.get("lastDigits")
    assert getattr(
        parsed_payment_method_details, "exp_month", None
    ) == payment_method_details.get("expMonth")
    assert getattr(
        parsed_payment_method_details, "exp_year", None
    ) == payment_method_details.get("expYear")


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.CHARGE_SUCCESS,
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
def test_transaction_session_success_schema_invalid_payment_method_details(
    payment_method_details, result
):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
        "data": "test-data",
        "paymentMethodDetails": payment_method_details,
    }

    # when & then
    with pytest.raises(ValidationError):
        TransactionSessionSuccessSchema.model_validate(data)


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_FAILURE,
        TransactionEventType.CHARGE_FAILURE,
        TransactionEventType.AUTHORIZATION_ACTION_REQUIRED,
        TransactionEventType.CHARGE_ACTION_REQUIRED,
        TransactionEventType.REFUND_SUCCESS,
        TransactionEventType.CANCEL_SUCCESS,
    ],
)
def test_transaction_session_success_schema_invalid_result(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
        "data": "test-data",
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionSessionSuccessSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"] == ("result",)


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_FAILURE,
        TransactionEventType.CHARGE_FAILURE,
    ],
)
def test_transaction_session_failure_schema_valid_result(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
        "data": "test-data",
    }

    # when
    transaction = TransactionSessionFailureSchema.model_validate(data)

    # then
    assert transaction.result == result


@pytest.mark.parametrize(
    "result",
    [
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
        {
            "type": "CARD",
            "name": "Test Card",
            "brand": None,
            "firstDigits": None,
            "lastDigits": None,
            "expMonth": None,
            "expYear": None,
        },
    ],
)
def test_transaction_session_failure_schema_valid_payment_method_details(
    payment_method_details, result
):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
        "data": "test-data",
        "paymentMethodDetails": payment_method_details,
    }

    # when
    parsed_transaction = TransactionSessionFailureSchema.model_validate(data)

    # then

    assert parsed_transaction.result == result
    assert parsed_transaction.payment_method_details
    parsed_payment_method_details = parsed_transaction.payment_method_details

    assert parsed_payment_method_details.type == payment_method_details["type"].lower()
    assert parsed_payment_method_details.name == payment_method_details["name"]
    assert getattr(
        parsed_payment_method_details, "brand", None
    ) == payment_method_details.get("brand")
    assert getattr(
        parsed_payment_method_details, "first_digits", None
    ) == payment_method_details.get("firstDigits")
    assert getattr(
        parsed_payment_method_details, "last_digits", None
    ) == payment_method_details.get("lastDigits")
    assert getattr(
        parsed_payment_method_details, "exp_month", None
    ) == payment_method_details.get("expMonth")
    assert getattr(
        parsed_payment_method_details, "exp_year", None
    ) == payment_method_details.get("expYear")


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_ACTION_REQUIRED,
        TransactionEventType.CHARGE_ACTION_REQUIRED,
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
def test_transaction_session_failure_schema_invalid_payment_method_details(
    payment_method_details, result
):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
        "data": "test-data",
        "paymentMethodDetails": payment_method_details,
    }

    # when & then
    with pytest.raises(ValidationError):
        TransactionSessionFailureSchema.model_validate(data)


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.AUTHORIZATION_ACTION_REQUIRED,
        TransactionEventType.CHARGE_ACTION_REQUIRED,
        TransactionEventType.AUTHORIZATION_REQUEST,
        TransactionEventType.CHARGE_REQUEST,
        TransactionEventType.REFUND_SUCCESS,
        TransactionEventType.CANCEL_SUCCESS,
    ],
)
def test_transaction_session_failure_schema_invalid_result(result):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": result.upper(),
        "data": "test-data",
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionSessionFailureSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"] == ("result",)


@pytest.mark.parametrize(
    "data_value",
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
def test_transaction_session_base_schema_valid_data(data_value):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": TransactionEventType.AUTHORIZATION_SUCCESS.upper(),
        "data": data_value,
    }

    # when
    transaction = TransactionSessionBaseSchema.model_validate(data)

    # then
    assert transaction.data == data_value


@pytest.mark.parametrize(
    "data_value",
    [
        # Non-serializable object
        object(),
        # Set - not JSON serializable
        {1, 2, 3},
        # Function
        lambda x: x,
        # File handle
        open,
    ],
)
def test_transaction_session_base_schema_invalid_data(data_value):
    # given
    data = {
        "pspReference": "psp-123",
        "amount": Decimal("100.50"),
        "result": TransactionEventType.CHARGE_SUCCESS.upper(),
        "data": data_value,
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        TransactionSessionBaseSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"] == ("data",)


@pytest.mark.parametrize(
    "data_value",
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
def test_payment_gateway_initialize_schema_valid_data(data_value):
    # given
    data = {
        "data": data_value,
    }

    # when
    response = PaymentGatewayInitializeSessionSchema.model_validate(data)

    # then
    assert response.data == data_value


@pytest.mark.parametrize(
    "data_value",
    [
        # Non-serializable object
        object(),
        # Set - not JSON serializable
        {1, 2, 3},
        # Function
        lambda x: x,
        # File handle
        open,
    ],
)
def test_payment_gateway_initialize_schema_invalid_data(data_value):
    # given
    data = {
        "data": data_value,
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        PaymentGatewayInitializeSessionSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"] == ("data",)
