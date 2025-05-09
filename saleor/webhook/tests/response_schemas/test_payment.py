from unittest.mock import patch

import pytest
from pydantic import ValidationError

from ...response_schemas.payment import (
    CreditCardInfoSchema,
    ListStoredPaymentMethodsSchema,
    StoredPaymentMethodSchema,
)
from ...response_schemas.utils.annotations import logger as annotations_logger


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
