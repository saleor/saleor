import base64
from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest
from pydantic import ValidationError

from ...response_schemas.shipping import (
    ExcludedShippingMethodSchema,
    FilterShippingMethodsSchema,
    ListShippingMethodsSchema,
    ShippingMethodSchema,
    logger,
)
from ...response_schemas.utils.annotations import logger as annotations_logger
from ...transport.shipping_helpers import to_shipping_app_id


def decode_id(id):
    return base64.b64decode(id).decode()


@pytest.mark.parametrize(
    "data",
    [
        # All fields provided
        {
            "id": "1",
            "name": "Standard Shipping",
            "amount": Decimal("10.00"),
            "currency": "USD",
            "maximum_delivery_days": 5,
            "minimum_delivery_days": 2,
            "description": "Fast delivery",
            "metadata": {"key1": "value1", "key2": "value2"},
            "private_metadata": {"private_key": "private_value"},
        },
        # Optional fields not provided
        {
            "id": 2,
            "name": "Express Shipping",
            "amount": Decimal("20.00"),
            "currency": "EUR",
        },
        # Amount as str
        {
            "id": 2,
            "name": "Express Shipping",
            "amount": "20.00",
            "currency": "EUR",
        },
        # Amount as float
        {
            "id": "2",
            "name": "Express Shipping",
            "amount": 20.00,
            "currency": "EUR",
        },
        # Amount as int
        {
            "id": 2,
            "name": "Express Shipping",
            "amount": 20,
            "currency": "EUR",
        },
        # Metadata is empty, delivery days, and description as None
        {
            "id": "3",
            "name": "Overnight Shipping",
            "amount": Decimal("50.00"),
            "currency": "GBP",
            "maximum_delivery_days": None,
            "minimum_delivery_days": None,
            "description": None,
            "metadata": {},  # Empty metadata
            "private_metadata": {},  # Empty private metadata
        },
        # No description or metadata
        {
            "id": "4",
            "name": "Free Shipping",
            "amount": Decimal("0.00"),
            "currency": "USD",
            "maximum_delivery_days": 7,
            "minimum_delivery_days": 5,
        },
        # Metadata is None
        {
            "id": 5,
            "name": "International Shipping",
            "amount": Decimal("30.00"),
            "currency": "USD",
            "description": None,
            "metadata": None,
            "private_metadata": None,
        },
    ],
)
def test_shipping_method_schema_valid(data, app):
    # when
    shipping_method_model = ShippingMethodSchema.model_validate(
        data, context={"app": app, "currency": data["currency"]}
    )

    # then
    assert shipping_method_model.id == to_shipping_app_id(app, data["id"])
    assert shipping_method_model.name == data["name"]
    assert shipping_method_model.amount == Decimal(data["amount"])
    assert shipping_method_model.currency == data["currency"]
    assert shipping_method_model.maximum_delivery_days == data.get(
        "maximum_delivery_days"
    )
    assert shipping_method_model.minimum_delivery_days == data.get(
        "minimum_delivery_days"
    )
    assert shipping_method_model.description == data.get("description")
    assert shipping_method_model.metadata == (data.get("metadata") or {})
    assert shipping_method_model.private_metadata == (
        data.get("private_metadata") or {}
    )


@pytest.mark.parametrize(
    "metadata", [12345, "not_a_dict", {123: 123}, {"123": 123}, {123: "123"}]
)
def test_shipping_method_schema_invalid_metadata_skipped(metadata, app):
    # given
    data = {
        "id": "4",
        "name": "Free Shipping",
        "amount": Decimal("0.00"),
        "currency": "USD",
        "metadata": metadata,
    }

    # when
    shipping_method_model = ShippingMethodSchema.model_validate(
        data, context={"app": app, "currency": data["currency"]}
    )

    # then
    assert shipping_method_model.id == to_shipping_app_id(app, data["id"])
    assert shipping_method_model.name == data["name"]
    assert shipping_method_model.amount == data["amount"]
    assert shipping_method_model.currency == data["currency"]
    assert shipping_method_model.maximum_delivery_days is None
    assert shipping_method_model.minimum_delivery_days is None
    assert shipping_method_model.description is None
    assert shipping_method_model.metadata == {}


@pytest.mark.parametrize(
    "private_metadata", [12345, "not_a_dict", {123: 123}, {"123": 123}, {123: "123"}]
)
def test_shipping_method_schema_invalid_private_metadata_skipped(private_metadata, app):
    # given
    data = {
        "id": "4",
        "name": "Free Shipping",
        "amount": Decimal("0.00"),
        "currency": "USD",
        "private_metadata": private_metadata,
    }

    # when
    shipping_method_model = ShippingMethodSchema.model_validate(
        data, context={"app": app, "currency": data["currency"]}
    )

    # then
    assert shipping_method_model.id == to_shipping_app_id(app, data["id"])
    assert shipping_method_model.name == data["name"]
    assert shipping_method_model.amount == data["amount"]
    assert shipping_method_model.currency == data["currency"]
    assert shipping_method_model.maximum_delivery_days is None
    assert shipping_method_model.minimum_delivery_days is None
    assert shipping_method_model.description is None
    assert shipping_method_model.metadata == {}
    assert shipping_method_model.private_metadata == {}


@pytest.mark.parametrize(
    ("data", "invalid_field"),
    [
        # Missing required fields - missing id
        (
            {
                "name": "Standard Shipping",
                "amount": Decimal("10.00"),
                "currency": "USD",
            },
            "id",
        ),
        # Missing required fields - missing name
        (
            {
                "id": 0,
                "amount": Decimal("10.00"),
                "currency": "USD",
            },
            "name",
        ),
        # Missing required fields - missing amount
        (
            {
                "id": 0,
                "name": "Standard Shipping",
                "currency": "USD",
            },
            "amount",
        ),
        # Missing required fields - missing currency
        (
            {
                "id": 0,
                "amount": Decimal("10.00"),
                "name": "Standard Shipping",
            },
            "currency",
        ),
        # Invalid type for "id"
        (
            {
                "id": {"invalid": "dict"},
                "name": "Standard Shipping",
                "amount": Decimal("10.00"),
                "currency": "USD",
            },
            "id",
        ),
        # Invalid type for "amount"
        (
            {
                "id": "1",
                "name": "Standard Shipping",
                "amount": "invalid_amount",
                "currency": "USD",
            },
            "amount",
        ),
        # Negative value for "amount"
        (
            {
                "id": "2",
                "name": "Express Shipping",
                "amount": Decimal("-10.00"),
                "currency": "USD",
            },
            "amount",
        ),
        # Invalid type for "maximum_delivery_days"
        (
            {
                "id": "5",
                "name": "International Shipping",
                "amount": Decimal("30.00"),
                "currency": "USD",
                "maximum_delivery_days": "invalid_days",
            },
            "maximum_delivery_days",
        ),
        # Invalid type for "minimum_delivery_days"
        (
            {
                "id": "5",
                "name": "International Shipping",
                "amount": Decimal("30.00"),
                "currency": "USD",
                "minimum_delivery_days": "invalid_days",
            },
            "minimum_delivery_days",
        ),
        # Negative value for "maximum_delivery_days"
        (
            {
                "id": 6,
                "name": "Economy Shipping",
                "amount": Decimal("5.00"),
                "currency": "USD",
                "maximum_delivery_days": -1,
            },
            "maximum_delivery_days",
        ),
        # Negative value for "minimum_delivery_days"
        (
            {
                "id": 6,
                "name": "Economy Shipping",
                "amount": Decimal("5.00"),
                "currency": "USD",
                "minimum_delivery_days": -1,
            },
            "minimum_delivery_days",
        ),
        # Name exceeds max length
        (
            {
                "id": 7,
                "name": "A" * 300,
                "amount": Decimal("15.00"),
                "currency": "USD",
            },
            "name",
        ),
        # Currency mismatch
        (
            {
                "id": 0,
                "amount": Decimal("10.00"),
                "name": "Standard Shipping",
                "currency": "PLN",
            },
            "currency",
        ),
    ],
)
def test_shipping_method_schema_invalid(data, app, invalid_field):
    with pytest.raises(ValidationError) as exc_info:
        ShippingMethodSchema.model_validate(
            data, context={"app": app, "currency": "USD"}
        )

    assert len(exc_info.value.errors()) == 1
    assert exc_info.value.errors()[0]["loc"] == (invalid_field,)


@pytest.mark.parametrize("data", [None, []])
def test_list_shipping_methods_schema_skipped_values(data, app):
    # when
    list_methods = ListShippingMethodsSchema.model_validate(
        data, context={"app": app, "currency": "USD"}
    )

    # Then the root should be an empty list
    assert list_methods.root == []


@patch.object(annotations_logger, "warning")
def test_list_shipping_methods_schema_invalid_element_skipped(mocked_logger, app):
    """Test when the provided input has 2 elements, one valid and one invalid."""
    # given a list with one valid and one invalid shipping method
    data = [
        {
            "id": "1",
            "name": "Standard Shipping",
            "amount": Decimal("10.00"),
            "currency": "USD",
            "maximum_delivery_days": 5,
            "minimum_delivery_days": 2,
            "description": "Fast delivery",
            "metadata": {"key1": "value1", "key2": "value2"},
        },
        {
            "id": "2",
            "name": "Express Shipping",
            "amount": "invalid_amount",  # Invalid amount
            "currency": "USD",
        },
        {
            "id": "2",
            "name": "Express Shipping",
            "amount": Decimal("10.00"),
            "currency": "PLN",  # Currency mismatch
        },
    ]

    # when
    schema = ListShippingMethodsSchema.model_validate(
        data, context={"app": app, "currency": "USD"}
    )

    # then only the valid shipping method should be included
    assert len(schema.root) == 1
    assert schema.root[0].id == to_shipping_app_id(app, data[0]["id"])
    assert schema.root[0].name == data[0]["name"]
    assert mocked_logger.call_count == 2


@pytest.mark.parametrize(
    "data",
    [
        {"id": graphene.Node.to_global_id("app", "123"), "reason": "Some reason"},
        {"id": graphene.Node.to_global_id("app", "456"), "reason": None},
        {"id": graphene.Node.to_global_id("app", "789"), "reason": ""},
    ],
)
def test_excluded_shipping_method_schema_valid_external_method(data):
    # when
    excluded_method_data = ExcludedShippingMethodSchema.model_validate(data)

    # then
    assert excluded_method_data.id == data["id"]
    assert excluded_method_data.reason == (data["reason"] or "")


@pytest.mark.parametrize(
    "data",
    [
        {
            "id": graphene.Node.to_global_id("ShippingMethod", "123"),
            "reason": "Some reason",
        },
        {"id": graphene.Node.to_global_id("ShippingMethod", "456"), "reason": None},
        {"id": graphene.Node.to_global_id("ShippingMethod", "789"), "reason": ""},
    ],
)
def test_excluded_shipping_method_schema_valid_shipping_method(data):
    # when
    excluded_method_data = ExcludedShippingMethodSchema.model_validate(data)

    # then
    assert excluded_method_data.id == graphene.Node.from_global_id(data["id"])[1]
    assert excluded_method_data.reason == (data["reason"] or "")


@pytest.mark.parametrize(
    "id",
    [
        "invalid_id",
        "123",
        graphene.Node.to_global_id("ABC", "123"),
    ],
)
@patch.object(logger, "warning")
def test_excluded_shipping_method_schema_invalid_id(mocked_logger, id):
    # given
    data = {"id": id, "reason": "Some reason"}

    # when
    with pytest.raises(ValidationError):
        ExcludedShippingMethodSchema.model_validate(data)

    # then
    assert mocked_logger.call_count == 1


@pytest.mark.parametrize("data", [None, []])
def test_filter_shipping_methods_schema_skipped_values(data):
    # given
    input_data = {"excluded_methods": data}

    # when
    list_methods = FilterShippingMethodsSchema.model_validate(input_data)

    # Then the root should be an empty list
    assert list_methods.excluded_methods == []


@patch.object(logger, "warning")
def test_filter_shipping_methods_schema_invalid_element_skipped(mocked_logger):
    """Test when the provided input has 2 elements, one valid and one invalid."""
    # given a list with one valid and one invalid shipping method
    data = {
        "excluded_methods": [
            {
                "id": graphene.Node.to_global_id("app", "123"),
                "reason": "Some reason",
            },
            {
                "id": "INVALID",
                "reason": None,
            },
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "456"),
                "reason": None,
            },
        ]
    }

    # when
    schema = FilterShippingMethodsSchema.model_validate(
        data,
        context={
            "custom_message": "Custom error while validating stored payment methods"
        },
    )

    # then only the valid shipping method should be included
    assert len(schema.excluded_methods) == 2
    assert schema.excluded_methods[0].id == data["excluded_methods"][0]["id"]
    assert schema.excluded_methods[0].reason == data["excluded_methods"][0]["reason"]
    assert (
        schema.excluded_methods[1].id
        == graphene.Node.from_global_id(data["excluded_methods"][2]["id"])[1]
    )
    assert schema.excluded_methods[1].reason == ""
