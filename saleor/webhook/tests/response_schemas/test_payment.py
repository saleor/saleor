from unittest.mock import patch

import pytest
from pydantic import ValidationError

from ....payment.interface import (
    PaymentGatewayInitializeTokenizationResult,
    PaymentMethodTokenizationResult,
    StoredPaymentMethodRequestDeleteResult,
)
from ...response_schemas.payment import (
    CreditCardInfoSchema,
    ListStoredPaymentMethodsSchema,
    PaymentGatewayInitializeTokenizationSessionSchema,
    PaymentMethodTokenizationFailedSchema,
    PaymentMethodTokenizationPendingSchema,
    PaymentMethodTokenizationSuccessSchema,
    StoredPaymentMethodDeleteRequestedSchema,
    StoredPaymentMethodSchema,
)
from ...response_schemas.utils.annotations import logger as annotations_logger
from ...transport.utils import to_payment_app_id


@pytest.mark.parametrize(
    "data",
    [
        # All fields
        {
            "brand": "visa",
            "lastDigits": "1234",
            "expYear": 2023,
            "expMonth": 12,
            "firstDigits": "123456",
        },
        # Only required fields
        {
            "brand": "mastercard",
            "lastDigits": "5678",
            "expYear": 2025,
            "expMonth": 6,
        },
        # All int fields as strings
        {
            "brand": "visa",
            "lastDigits": "1234",
            "expYear": "2023",
            "expMonth": "12",
            "firstDigits": "123456",
        },
        # All digit fields as int
        {
            "brand": "visa",
            "lastDigits": 1234,
            "expYear": 2023,
            "expMonth": 12,
            "firstDigits": 123456,
        },
    ],
)
def test_credit_card_info_schema_valid(data):
    # when
    schema = CreditCardInfoSchema.model_validate(data)

    # then
    assert schema.brand == data["brand"]
    assert schema.last_digits == str(data["lastDigits"])
    assert schema.exp_year == int(data["expYear"])
    assert schema.exp_month == int(data["expMonth"])
    first_digits = data.get("firstDigits")
    assert schema.first_digits == (str(first_digits) if first_digits else None)


class NonParsableObject:
    def __str__(self):
        raise ValueError("Cannot convert to string")


@pytest.mark.parametrize(
    ("data", "invalid_field"),
    [
        # Missing `brand` field
        (
            {
                "lastDigits": "1234",
                "expYear": 2023,
                "expMonth": 12,
                "firstDigits": "123456",
            },
            "brand",
        ),
        # Missing `lastDigits` field
        (
            {
                "brand": "visa",
                "expYear": 2023,
                "expMonth": 12,
                "firstDigits": "123456",
            },
            "lastDigits",
        ),
        # Missing `expYear` field
        (
            {
                "brand": "visa",
                "expMonth": 12,
                "lastDigits": "1234",
            },
            "expYear",
        ),
        # Missing `expMonth` field
        (
            {
                "brand": "visa",
                "expYear": 2023,
                "lastDigits": "1234",
            },
            "expMonth",
        ),
        # Not parsable `expYear`
        (
            {
                "brand": "visa",
                "lastDigits": "1234",
                "expYear": "ABC",
                "expMonth": 12,
                "firstDigits": "123456",
            },
            "expYear",
        ),
        # Not parsable `expMonth`
        (
            {
                "brand": "visa",
                "lastDigits": "1234",
                "expYear": 2023,
                "expMonth": "ABC",
                "firstDigits": "123456",
            },
            "expMonth",
        ),
        # Empty string as `expYear`
        (
            {
                "brand": "visa",
                "lastDigits": "1234",
                "expYear": "",
                "expMonth": 12,
                "firstDigits": "123456",
            },
            "expYear",
        ),
        # Empty string as `expMonth`
        (
            {
                "brand": "visa",
                "lastDigits": "1234",
                "expYear": 2023,
                "expMonth": "",
                "firstDigits": "123456",
            },
            "expMonth",
        ),
        # None as `lastDigits`
        (
            {
                "brand": "visa",
                "lastDigits": None,
                "expYear": 2023,
                "expMonth": 12,
                "firstDigits": "123456",
            },
            "lastDigits",
        ),
        # Not parsable as `lastDigits`
        (
            {
                "brand": "visa",
                "lastDigits": NonParsableObject(),
                "expYear": 2023,
                "expMonth": 12,
                "firstDigits": "123456",
            },
            "lastDigits",
        ),
        # Not parsable as `firstDigits`
        (
            {
                "brand": "visa",
                "lastDigits": "1234",
                "expYear": 2023,
                "expMonth": 12,
                "firstDigits": NonParsableObject(),
            },
            "firstDigits",
        ),
    ],
)
def test_credit_card_info_schema_invalid(data, invalid_field):
    # when
    with pytest.raises(ValidationError) as exc_info:
        CreditCardInfoSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"][0] == invalid_field


@pytest.mark.parametrize(
    "field",
    [
        "brand",
        "lastDigits",
        "expYear",
        "expMonth",
    ],
)
def test_credit_card_info_schema_required_field_is_none(field):
    # given
    data = {
        "brand": "visa",
        "lastDigits": "1234",
        "expYear": 2023,
        "expMonth": 12,
        "firstDigits": "123456",
    }
    data[field] = None

    # when
    with pytest.raises(ValidationError) as exc_info:
        CreditCardInfoSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"][0] == field


@pytest.mark.parametrize(
    "data",
    [
        # All fields
        {
            "id": "method-1",
            "supportedPaymentFlows": ["INTERACTIVE"],
            "type": "Credit Card",
            "name": "Visa ***1234",
            "data": {"key": "value"},
            "creditCardInfo": {
                "brand": "visa",
                "lastDigits": "1234",
                "expYear": 2023,
                "expMonth": 12,
                "firstDigits": "123456",
            },
        },
        # Only required fields
        {
            "id": "method-2",
            "type": "Credit Card",
        },
        # Empty not required fields
        {
            "id": "method-3",
            "supportedPaymentFlows": None,
            "type": "Credit Card",
            "name": None,
            "data": None,
            "creditCardInfo": None,
        },
        # Empty list as supportedPaymentFlows
        {
            "id": "method-4",
            "supportedPaymentFlows": [],
            "type": "Credit Card",
        },
    ],
)
def test_stored_payment_method_schema_valid(data):
    # when
    schema = StoredPaymentMethodSchema.model_validate(data)

    # then
    assert schema.id == data["id"]
    assert schema.supported_payment_flows == [
        flow.lower() for flow in data.get("supportedPaymentFlows") or []
    ]
    assert schema.type == data["type"]
    assert schema.name == data.get("name")
    assert schema.data == data.get("data")
    if "creditCardInfo" in data and data["creditCardInfo"]:
        assert schema.credit_card_info.brand == data["creditCardInfo"]["brand"]
        assert (
            schema.credit_card_info.last_digits == data["creditCardInfo"]["lastDigits"]
        )
        assert schema.credit_card_info.exp_year == data["creditCardInfo"]["expYear"]
        assert schema.credit_card_info.exp_month == data["creditCardInfo"]["expMonth"]
        assert (
            schema.credit_card_info.first_digits
            == data["creditCardInfo"]["firstDigits"]
        )
    else:
        assert schema.credit_card_info is None


@pytest.mark.parametrize(
    ("data", "invalid_field"),
    [
        # Missing `id` field
        (
            {
                "supportedPaymentFlows": ["INTERACTIVE"],
                "type": "Credit Card",
            },
            "id",
        ),
        # Invalid `supportedPaymentFlows`
        (
            {
                "id": "method-1",
                "supportedPaymentFlows": ["INVALID_FLOW"],
                "type": "Credit Card",
            },
            "supportedPaymentFlows",
        ),
        # Missing `type` field
        (
            {
                "id": "method-1",
                "supportedPaymentFlows": ["INTERACTIVE"],
            },
            "type",
        ),
        # Not parable `data` field
        (
            {
                "id": "method-1",
                "supportedPaymentFlows": ["INTERACTIVE"],
                "type": "Credit Card",
                "data": object(),
            },
            "data",
        ),
    ],
)
def test_stored_payment_method_schema_invalid(data, invalid_field):
    # when
    with pytest.raises(ValidationError) as exc_info:
        StoredPaymentMethodSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"][0] == invalid_field


@patch.object(annotations_logger, "warning")
def test_stored_payment_method_schema_invalid_credit_card_info_skipped(
    mocked_logger, app
):
    # given
    id = "method-1"
    type = "Credit Card"

    # when
    schema = StoredPaymentMethodSchema.model_validate(
        {
            "id": id,
            "type": type,
            "creditCardInfo": {
                "brand": "visa",
                "lastDigits": NonParsableObject(),
                "expYear": 2023,
                "expMonth": 12,
                "firstDigits": "123456",
            },
        },
        context={
            "app": app,
        },
    )

    # then
    assert schema.credit_card_info is None
    assert schema.id == id
    assert schema.type == type
    assert mocked_logger.call_count == 1
    error_msg = mocked_logger.call_args[0][0]
    assert "Skipping invalid value" in error_msg
    assert mocked_logger.call_args[1]["extra"]["app"] == app.id
    assert mocked_logger.call_args[1]["extra"]["field_name"] == "credit_card_info"


@pytest.mark.parametrize(
    "data",
    [
        # All fields
        {
            "paymentMethods": [
                {
                    "id": "method-1",
                    "supportedPaymentFlows": ["INTERACTIVE"],
                    "type": "Credit Card",
                    "name": "Visa ***1234",
                    "data": {"key": "value"},
                    "creditCardInfo": {
                        "brand": "visa",
                        "lastDigits": "1234",
                        "expYear": 2023,
                        "expMonth": 12,
                        "firstDigits": "123456",
                    },
                },
                {
                    "id": "method-2",
                    "supportedPaymentFlows": ["INTERACTIVE"],
                    "type": "Debit Card",
                },
            ]
        },
        # Empty list ad paymentMethods
        {"paymentMethods": []},
        # None as paymentMethods
        {"paymentMethods": None},
        # Only required fields
        {
            "paymentMethods": [
                {
                    "id": "method-3",
                    "type": "Credit Card",
                }
            ]
        },
    ],
)
def test_list_stored_payment_methods_schema_valid(data):
    # when
    schema = ListStoredPaymentMethodsSchema.model_validate(data)

    # then
    assert len(schema.payment_methods) == (
        len(data["paymentMethods"]) if data["paymentMethods"] else 0
    )


@pytest.mark.parametrize(
    "data",
    [{}, {"test": "invalid"}],
)
def test_list_stored_payment_methods_schema_invalid(data):
    # when
    schema = ListStoredPaymentMethodsSchema.model_validate(data)

    # then
    assert schema.payment_methods == []


@patch.object(annotations_logger, "warning")
def test_list_stored_payment_methods_schema_invalid_element_skipped(mocked_logger):
    """Test when the input has one valid and one invalid stored payment method."""
    # given a list with one valid and one invalid payment method
    data = {
        "paymentMethods": [
            {
                "id": "method-1",
                "supportedPaymentFlows": ["INTERACTIVE"],
                "type": "Credit Card",
                "name": "Visa ***1234",
            },
            # missing type
            {
                "id": "method-2",
                "name": "Visa ***4321",
            },
        ]
    }

    # when
    schema = ListStoredPaymentMethodsSchema.model_validate(data)

    # then only the valid payment method should be included
    assert len(schema.payment_methods) == 1
    assert schema.payment_methods[0].id == data["paymentMethods"][0]["id"]
    assert schema.payment_methods[0].name == data["paymentMethods"][0]["name"]
    assert mocked_logger.call_count == 1


@pytest.mark.parametrize(
    "data",
    [
        # Successfully deleted
        {
            "result": StoredPaymentMethodRequestDeleteResult.SUCCESSFULLY_DELETED.name,
            "error": None,
        },
        # Failed to delete with error message
        {
            "result": StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELETE.name,
            "error": "Some error occurred",
        },
        # Failed to deliver with error message
        {
            "result": StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELIVER.name,
            "error": "Delivery failed due to network issues",
        },
        # Failed to delete no error message
        {
            "result": StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELETE.name,
        },
        # Failed to deliver no error message
        {
            "result": StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELIVER.name,
        },
    ],
)
def test_stored_payment_method_delete_requested_schema_valid(data):
    # when
    schema = StoredPaymentMethodDeleteRequestedSchema.model_validate(data)

    # then
    assert schema.result == data["result"].lower()
    assert schema.error == data.get("error")


@pytest.mark.parametrize(
    ("data", "invalid_field"),
    [
        # Missing `result` field
        (
            {
                "error": "Some error occurred",
            },
            "result",
        ),
        # Lower value for `result`
        (
            {
                "result": "successfully_deleted",
                "error": "Some error occurred",
            },
            "result",
        ),
        # Invalid `result` value
        (
            {
                "result": "INVALID_RESULT",
                "error": "Invalid result value",
            },
            "result",
        ),
        # Invalid `error` type
        (
            {
                "result": StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELETE.name,
                "error": 123,  # Should be a string or None
            },
            "error",
        ),
    ],
)
def test_stored_payment_method_delete_requested_schema_invalid(data, invalid_field):
    # when
    with pytest.raises(ValidationError) as exc_info:
        StoredPaymentMethodDeleteRequestedSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"][0] == invalid_field


@pytest.mark.parametrize(
    "data",
    [
        # Successfully initialize
        {
            "result": PaymentGatewayInitializeTokenizationResult.SUCCESSFULLY_INITIALIZED.name,
            "error": None,
            "data": {"key": "value"},
        },
        # Successfully initialize data as string
        {
            "result": PaymentGatewayInitializeTokenizationResult.SUCCESSFULLY_INITIALIZED.name,
            "data": "Successfully initialized",
        },
        # Failed to initialize with error message
        {
            "result": PaymentGatewayInitializeTokenizationResult.FAILED_TO_INITIALIZE.name,
            "error": "Some error occurred",
            "data": None,
        },
        # Failed to deliver with error message
        {
            "result": PaymentGatewayInitializeTokenizationResult.FAILED_TO_DELIVER.name,
            "error": "Delivery failed due to network issues",
        },
        # Failed to initialize no error message
        {
            "result": PaymentGatewayInitializeTokenizationResult.FAILED_TO_INITIALIZE.name,
            "data": None,
            "error": None,
        },
        # Failed to deliver no error message
        {
            "result": PaymentGatewayInitializeTokenizationResult.FAILED_TO_DELIVER.name,
        },
    ],
)
def test_payment_gateway_initialize_tokenization_session_schema_valid(data):
    # when
    schema = PaymentGatewayInitializeTokenizationSessionSchema.model_validate(data)

    # then
    assert schema.result == data["result"].lower()
    assert schema.data == data.get("data")
    assert schema.error == data.get("error")


@pytest.mark.parametrize(
    ("data", "invalid_field"),
    [
        # Missing `result` field
        (
            {
                "error": "Some error occurred",
            },
            "result",
        ),
        # Lower value for `result`
        (
            {
                "result": PaymentGatewayInitializeTokenizationResult.SUCCESSFULLY_INITIALIZED.value,
                "error": "Some error occurred",
            },
            "result",
        ),
        # Invalid `result` value
        (
            {
                "result": "INVALID_RESULT",
                "error": "Invalid result value",
            },
            "result",
        ),
        # Invalid `error` type
        (
            {
                "result": PaymentGatewayInitializeTokenizationResult.FAILED_TO_INITIALIZE.name,
                "error": 123,  # Should be a string or None
            },
            "error",
        ),
        # Not parsable `data`
        (
            {
                "result": PaymentGatewayInitializeTokenizationResult.FAILED_TO_INITIALIZE.name,
                "error": "error",
                "data": object(),
            },
            "data",
        ),
    ],
)
def test_payment_gateway_initialize_tokenization_session_schema_invalid(
    data, invalid_field
):
    # when
    with pytest.raises(ValidationError) as exc_info:
        PaymentGatewayInitializeTokenizationSessionSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"][0] == invalid_field


@pytest.mark.parametrize(
    "data",
    [
        # SUCCESSFULLY_TOKENIZED with not data and no error
        {
            "id": "123",
            "result": PaymentMethodTokenizationResult.SUCCESSFULLY_TOKENIZED.name,
        },
        # ADDITIONAL_ACTION_REQUIRED with data
        {
            "id": "456",
            "result": PaymentMethodTokenizationResult.ADDITIONAL_ACTION_REQUIRED.name,
            "data": {"action": "verify"},
        },
    ],
)
def test_payment_method_tokenization_schema_valid(data, app):
    # when
    schema = PaymentMethodTokenizationSuccessSchema.model_validate(
        data, context={"app": app}
    )

    # then
    assert schema.result == PaymentMethodTokenizationResult[data["result"]]
    assert schema.data == data.get("data")
    assert schema.id == to_payment_app_id(app, data["id"])


def test_payment_method_tokenization_schema_valid_extra_data_in_input(app):
    # given
    data = {
        "id": "123",
        "result": PaymentMethodTokenizationResult.SUCCESSFULLY_TOKENIZED.name,
        "error": "extra error value",
        "data": {"key": "value"},
    }

    # when
    schema = PaymentMethodTokenizationSuccessSchema.model_validate(
        data, context={"app": app}
    )

    # then
    assert schema.result == PaymentMethodTokenizationResult[data["result"]]
    assert schema.data == data.get("data")
    assert schema.id == to_payment_app_id(app, data["id"])


@pytest.mark.parametrize(
    ("data", "expected_error_field"),
    [
        # Missing `id` field
        (
            {
                "result": PaymentMethodTokenizationResult.SUCCESSFULLY_TOKENIZED.name,
                "data": {"key": "value"},
            },
            "id",
        ),
        # Missing `result` field
        (
            {
                "id": "123",
                "data": {"key": "value"},
                "error": None,
            },
            "result",
        ),
        # Invalid `result` value
        (
            {
                "id": "123",
                "result": "INVALID_RESULT",
            },
            "result",
        ),
        # `id` field with wrong type
        (
            {
                "id": 123,
                "result": PaymentMethodTokenizationResult.SUCCESSFULLY_TOKENIZED.name,
                "data": {"key": "value"},
                "error": None,
            },
            "id",
        ),
    ],
)
def test_payment_method_tokenization_schema_invalid(data, expected_error_field, app):
    # when
    with pytest.raises(ValidationError) as exc_info:
        PaymentMethodTokenizationSuccessSchema.model_validate(
            data, context={"app": app}
        )

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"][0] == expected_error_field


@pytest.mark.parametrize(
    "data",
    [
        # All fields provided
        {
            "id": "123",
            "result": PaymentMethodTokenizationResult.PENDING.name,
            "data": {"status": "pending"},
        },
        # `id` is None
        {
            "id": None,
            "result": PaymentMethodTokenizationResult.PENDING.name,
            "data": {"status": "pending"},
        },
        # No data provided
        {
            "id": "456",
            "result": PaymentMethodTokenizationResult.PENDING.name,
        },
    ],
)
def test_payment_method_tokenization_pending_schema_valid(data, app):
    # when
    schema = PaymentMethodTokenizationPendingSchema.model_validate(
        data, context={"app": app}
    )

    # then
    assert schema.result == PaymentMethodTokenizationResult.PENDING
    assert schema.data == data.get("data", None)
    assert schema.id == (to_payment_app_id(app, data["id"]) if data["id"] else None)


@pytest.mark.parametrize(
    ("data", "expected_error_field"),
    [
        # Missing `result` field
        (
            {
                "id": "123",
                "data": {"status": "pending"},
            },
            "result",
        ),
        # Invalid `result` value
        (
            {
                "id": "123",
                "result": "INVALID_RESULT",
                "data": {"status": "pending"},
            },
            "result",
        ),
        # `id` field with wrong type
        (
            {
                "id": 123,
                "result": PaymentMethodTokenizationResult.PENDING.name,
                "data": {"status": "pending"},
            },
            "id",
        ),
    ],
)
def test_payment_method_tokenization_pending_schema_invalid(data, expected_error_field):
    # when
    with pytest.raises(ValidationError) as exc_info:
        PaymentMethodTokenizationPendingSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"][0] == expected_error_field


@pytest.mark.parametrize(
    "data",
    [
        # `FAILED_TO_TOKENIZE`` with error message
        {
            "result": PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE.name,
            "error": "Tokenization failed.",
        },
        # `FAILED_TO_DELIVER`` with error message
        {
            "result": PaymentMethodTokenizationResult.FAILED_TO_DELIVER.name,
            "error": "Tokenization failed.",
        },
        # `FAILED_TO_TOKENIZE` without error message
        {
            "result": PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE.name,
            "error": None,
        },
        # `FAILED_TO_DELIVER` without error message
        {
            "result": PaymentMethodTokenizationResult.FAILED_TO_DELIVER.name,
        },
    ],
)
def test_payment_method_tokenization_failed_schema_valid(data):
    # when
    schema = PaymentMethodTokenizationFailedSchema.model_validate(data)

    # then
    assert schema.result == PaymentMethodTokenizationResult[data["result"]]
    assert schema.error == data.get("error")


@pytest.mark.parametrize(
    ("data", "expected_error_field"),
    [
        # Missing `result` field
        (
            {
                "error": "Tokenization failed due to invalid input.",
            },
            "result",
        ),
        # Invalid `result` value
        (
            {
                "result": "INVALID_RESULT",
                "error": "Invalid result value.",
            },
            "result",
        ),
        # `error` field with wrong type
        (
            {
                "result": PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE.name,
                "error": 123,  # Should be a string or None
            },
            "error",
        ),
    ],
)
def test_payment_method_tokenization_failed_schema_invalid(data, expected_error_field):
    # when
    with pytest.raises(ValidationError) as exc_info:
        PaymentMethodTokenizationFailedSchema.model_validate(data)

    # then
    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"][0] == expected_error_field
