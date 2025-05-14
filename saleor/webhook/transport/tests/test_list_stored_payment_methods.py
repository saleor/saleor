import copy
from unittest.mock import patch

import pytest

from ....payment.interface import (
    PaymentGateway,
    PaymentGatewayInitializeTokenizationResult,
    PaymentMethodCreditCardInfo,
    PaymentMethodData,
    PaymentMethodTokenizationResult,
    StoredPaymentMethodRequestDeleteResult,
)
from ...response_schemas.utils.annotations import logger as annotations_logger
from ..list_stored_payment_methods import (
    get_list_stored_payment_methods_from_response,
    get_response_for_payment_gateway_initialize_tokenization,
    get_response_for_payment_method_tokenization,
    get_response_for_stored_payment_method_request_delete,
    logger,
)
from ..utils import to_payment_app_id


@patch.object(annotations_logger, "warning")
def test_get_list_stored_payment_methods_from_response(mocked_logger, app):
    # given
    payment_method_response = {
        "id": "method-1",
        "supportedPaymentFlows": ["INTERACTIVE"],
        "type": "Credit Card",
        "creditCardInfo": {
            "brand": "visa",
            "lastDigits": "1234",
            "expMonth": 1,
            "expYear": 2023,
            "firstDigits": "123456",
        },
        "name": "***1234",
        "data": {"some": "data"},
    }
    # invalid second payment method due to to missing id
    second_payment_method = copy.deepcopy(payment_method_response)
    del second_payment_method["id"]

    list_stored_payment_methods_response = {
        "paymentMethods": [payment_method_response, second_payment_method]
    }
    currency = "usd"

    # when
    response = get_list_stored_payment_methods_from_response(
        app, list_stored_payment_methods_response, currency
    )

    # then
    assert len(response) == 1
    assert response[0] == PaymentMethodData(
        id=to_payment_app_id(app, payment_method_response["id"]),
        external_id=payment_method_response["id"],
        supported_payment_flows=[
            flow.lower()
            for flow in payment_method_response.get("supportedPaymentFlows", [])
        ],
        type=payment_method_response["type"],
        credit_card_info=PaymentMethodCreditCardInfo(
            brand=payment_method_response["creditCardInfo"]["brand"],
            last_digits=payment_method_response["creditCardInfo"]["lastDigits"],
            exp_year=payment_method_response["creditCardInfo"]["expYear"],
            exp_month=payment_method_response["creditCardInfo"]["expMonth"],
            first_digits=payment_method_response["creditCardInfo"].get("firstDigits"),
        )
        if payment_method_response.get("creditCardInfo")
        else None,
        name=payment_method_response["name"],
        data=payment_method_response["data"],
        gateway=PaymentGateway(
            id=app.identifier,
            name=app.name,
            currencies=[currency],
            config=[],
        ),
    )
    assert mocked_logger.call_count == 1
    error_msg = mocked_logger.call_args[0][1]
    assert error_msg == "Skipping invalid stored payment method"
    assert mocked_logger.call_args[1]["extra"]["app"] == app.id


def test_get_list_stored_payment_methods_from_response_only_required_fields(app):
    # given
    payment_method_response = {
        "id": "method-1",
        "type": "Credit Card",
    }

    list_stored_payment_methods_response = {"paymentMethods": [payment_method_response]}
    currency = "usd"

    # when
    response = get_list_stored_payment_methods_from_response(
        app, list_stored_payment_methods_response, currency
    )

    # then
    assert len(response) == 1
    assert response[0] == PaymentMethodData(
        id=to_payment_app_id(app, payment_method_response["id"]),
        external_id=payment_method_response["id"],
        supported_payment_flows=[],
        type=payment_method_response["type"],
        credit_card_info=None,
        gateway=PaymentGateway(
            id=app.identifier,
            name=app.name,
            currencies=[currency],
            config=[],
        ),
    )


@patch.object(logger, "warning")
def test_get_list_stored_payment_methods_from_response_invalid_input_data(
    mocked_logger, app
):
    # given
    list_stored_payment_methods_response = None
    currency = "usd"

    # when
    response = get_list_stored_payment_methods_from_response(
        app, list_stored_payment_methods_response, currency
    )

    # then
    assert response == []
    assert mocked_logger.call_count == 1
    error_msg = mocked_logger.call_args[0][0]
    assert "Skipping stored payment methods from app" in error_msg
    assert mocked_logger.call_args[1]["extra"]["app"] == app.id


@pytest.mark.parametrize(
    "response_data",
    [
        # Response with SUCCESSFULLY_DELETED result
        {
            "result": StoredPaymentMethodRequestDeleteResult.SUCCESSFULLY_DELETED.name,
            "error": None,
        },
        # Response with FAILED_TO_DELETE result and error
        {
            "result": StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELETE.name,
            "error": "Some error occurred",
        },
        # Response with FAILED_TO_DELIVER result and error
        {
            "result": StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELIVER.name,
            "error": "Some error occurred",
        },
        # Response with FAILED_TO_DELETE result no error
        {"result": StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELETE.name},
        # Response with FAILED_TO_DELETE result error as None
        {
            "result": StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELIVER.name,
            "error": None,
        },
    ],
)
def test_get_response_for_stored_payment_method_request_delete_valid_response(
    response_data,
):
    # when
    response = get_response_for_stored_payment_method_request_delete(response_data)

    # then
    assert response.result.name == response_data["result"]
    assert response.error == response_data.get("error")


@pytest.mark.parametrize(
    ("response_data", "expected_error"),
    [
        # Missing `result` in response
        (
            {"error": "Missing result"},
            "Missing value for field: result. Input: {'error': 'Missing result'}.",
        ),
        # Invalid `result` value
        (
            {"result": "INVALID_RESULT", "error": "Invalid result value"},
            "Incorrect value (INVALID_RESULT) for field: result. Error: Value error, "
            "Enum name not found: INVALID_RESULT.",
        ),
    ],
)
def test_get_response_for_stored_payment_method_request_delete_invalid_response(
    response_data, expected_error
):
    # when
    response = get_response_for_stored_payment_method_request_delete(response_data)

    # then
    assert (
        response.result.name
        == StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELETE.name
    )
    assert expected_error in response.error


def test_get_response_for_stored_payment_method_request_delete_response_is_none():
    # when
    response = get_response_for_stored_payment_method_request_delete(None)

    # then
    assert response.result == StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELIVER
    assert response.error == "Failed to delivery request."


@pytest.mark.parametrize(
    ("response_data"),
    [
        # Response with SUCCESSFULLY_INITIALIZED result and data
        {
            "result": PaymentGatewayInitializeTokenizationResult.SUCCESSFULLY_INITIALIZED.name,
            "data": {"foo": "bar"},
        },
        # Response with SUCCESSFULLY_INITIALIZED result and no data
        {
            "result": PaymentGatewayInitializeTokenizationResult.SUCCESSFULLY_INITIALIZED.name,
        },
        # Response with FAILED_TO_INITIALIZE result and error
        {
            "result": PaymentGatewayInitializeTokenizationResult.FAILED_TO_INITIALIZE.name,
            "error": "Some error occurred",
        },
        # Response with FAILED_TO_DELIVER result, error and data as None
        {
            "result": PaymentGatewayInitializeTokenizationResult.FAILED_TO_DELIVER.name,
            "error": None,
            "data": None,
        },
    ],
)
def test_get_response_for_payment_gateway_initialize_tokenization_valid_response(
    response_data,
):
    # when
    response = get_response_for_payment_gateway_initialize_tokenization(response_data)

    # then
    assert response.result.name == response_data["result"]
    assert response.error == response_data.get("error")
    assert response.data == response_data.get("data")


@pytest.mark.parametrize(
    ("response_data", "expected_error"),
    [
        # Missing `result` in response
        (
            {"error": "Missing result"},
            "Missing value for field: result. Input: {'error': 'Missing result'}.",
        ),
        # Invalid `result` value
        (
            {"result": "INVALID_RESULT", "error": "Invalid result value"},
            "Incorrect value (INVALID_RESULT) for field: result. Error: Value error, "
            "Enum name not found: INVALID_RESULT.",
        ),
    ],
)
def test_get_response_for_payment_gateway_initialize_tokenization_invalid_response(
    response_data, expected_error
):
    # when
    response = get_response_for_payment_gateway_initialize_tokenization(response_data)

    # then
    assert (
        response.result
        == PaymentGatewayInitializeTokenizationResult.FAILED_TO_INITIALIZE
    )
    assert response.error == expected_error


def test_get_response_for_payment_gateway_initialize_tokenization_response_is_none():
    # when
    response = get_response_for_payment_gateway_initialize_tokenization(None)

    # then
    assert (
        response.result == PaymentGatewayInitializeTokenizationResult.FAILED_TO_DELIVER
    )
    assert response.error == "Failed to delivery request."


@pytest.mark.parametrize(
    (
        "response_data",
        "expected_result",
        "expected_error",
        "expected_id",
        "expected_data",
    ),
    [
        # Successfully tokenized
        (
            {
                "id": "123",
                "result": PaymentMethodTokenizationResult.SUCCESSFULLY_TOKENIZED.name,
                "data": {"key": "value"},
                "error": None,
            },
            PaymentMethodTokenizationResult.SUCCESSFULLY_TOKENIZED,
            None,
            "123",
            {"key": "value"},
        ),
        # Additional action required
        (
            {
                "id": "456",
                "result": PaymentMethodTokenizationResult.ADDITIONAL_ACTION_REQUIRED.name,
                "data": {"action": "verify"},
                "error": None,
            },
            PaymentMethodTokenizationResult.ADDITIONAL_ACTION_REQUIRED,
            None,
            "456",
            {"action": "verify"},
        ),
        # Pending
        (
            {
                "result": PaymentMethodTokenizationResult.PENDING.name,
                "data": {"status": "pending"},
            },
            PaymentMethodTokenizationResult.PENDING,
            None,
            None,
            {"status": "pending"},
        ),
        # Failed to tokenize
        (
            {
                "result": PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE.name,
                "error": "Tokenization failed",
            },
            PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE,
            "Tokenization failed",
            None,
            None,
        ),
        # Invalid result
        (
            {"result": "INVALID_RESULT"},
            PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE,
            "Missing or invalid value for `result`: INVALID_RESULT. Possible values: "
            f"{', '.join([value.name for value in PaymentMethodTokenizationResult])}.",
            None,
            None,
        ),
        # No response data
        (
            None,
            PaymentMethodTokenizationResult.FAILED_TO_DELIVER,
            "Failed to delivery request.",
            None,
            None,
        ),
    ],
)
def test_get_response_for_payment_method_tokenization(
    response_data, expected_result, expected_error, expected_id, expected_data, app
):
    # when
    response = get_response_for_payment_method_tokenization(response_data, app)

    # then
    assert response.result == expected_result
    assert response.error == expected_error
    assert response.id == (to_payment_app_id(app, expected_id) if expected_id else None)
    assert response.data == expected_data


@pytest.mark.parametrize(
    ("response_data", "error_msg"),
    [
        # Missing `id` in success response
        (
            {
                "result": PaymentMethodTokenizationResult.SUCCESSFULLY_TOKENIZED.name,
                "data": {"key": "value"},
            },
            "Missing value for field: id. Input: ",
        ),
        # `id` as int for pending response
        (
            {
                "result": PaymentMethodTokenizationResult.PENDING.name,
                "id": 123,
            },
            "Incorrect value (123) for field: id. Error: Input should be a valid string.",
        ),
        # Invalid `error` in failed response
        (
            {
                "result": PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE.name,
                "error": 123,
            },
            "Incorrect value (123) for field: error. Error: Input should be a valid string.",
        ),
    ],
)
def test_get_response_for_payment_method_tokenization_validation_error(
    response_data, error_msg, app
):
    # when
    response = get_response_for_payment_method_tokenization(response_data, app)

    # then
    assert response.result == PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE
    assert error_msg in response.error


def test_get_response_for_payment_method_tokenization_value_error(app):
    # given
    result = "INVALID_RESULT"
    response_data = {"result": result}

    # when
    response = get_response_for_payment_method_tokenization(response_data, app)

    # then
    assert response.result == PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE
    assert (
        f"Missing or invalid value for `result`: {result}. Possible values: "
        in response.error
    )
