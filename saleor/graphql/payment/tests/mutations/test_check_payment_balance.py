from unittest.mock import Mock, patch

from .....payment import PaymentError
from .....payment.error_codes import PaymentErrorCode
from .....plugins.manager import PluginsManager
from ....tests.utils import get_graphql_content
from ...mutations import PaymentCheckBalance

MUTATION_CHECK_PAYMENT_BALANCE = """
    mutation checkPaymentBalance($input: PaymentCheckBalanceInput!) {
        paymentCheckBalance(input: $input){
            data
            errors {
                code
                field
                message
            }
        }
    }
"""


@patch.object(PluginsManager, "check_payment_balance")
def test_payment_check_balance_mutation_validate_gateway_does_not_exist(
    check_payment_balance_mock, staff_api_client, check_payment_balance_input
):
    check_payment_balance_input["gatewayId"] = "mirumee.payments.not_existing_gateway"
    response = staff_api_client.post_graphql(
        MUTATION_CHECK_PAYMENT_BALANCE, {"input": check_payment_balance_input}
    )

    content = get_graphql_content(response)
    errors = content["data"]["paymentCheckBalance"]["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == PaymentErrorCode.NOT_SUPPORTED_GATEWAY.value.upper()
    assert errors[0]["field"] == "gatewayId"
    assert errors[0]["message"] == (
        "The gateway_id mirumee.payments.not_existing_gateway is not available."
    )

    assert check_payment_balance_mock.call_count == 0


@patch.object(PluginsManager, "check_payment_balance")
@patch.object(PaymentCheckBalance, "validate_gateway")
@patch("saleor.graphql.channel.utils.validate_channel")
def test_payment_check_balance_validate_not_supported_currency(
    _, __, check_payment_balance_mock, staff_api_client, check_payment_balance_input
):
    check_payment_balance_input["card"]["money"]["currency"] = "ABSTRACT_CURRENCY"
    response = staff_api_client.post_graphql(
        MUTATION_CHECK_PAYMENT_BALANCE, {"input": check_payment_balance_input}
    )

    content = get_graphql_content(response)
    errors = content["data"]["paymentCheckBalance"]["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == PaymentErrorCode.NOT_SUPPORTED_GATEWAY.value.upper()
    assert errors[0]["field"] == "currency"
    assert errors[0]["message"] == (
        "The currency ABSTRACT_CURRENCY is not "
        "available for mirumee.payments.gateway."
    )

    assert check_payment_balance_mock.call_count == 0


@patch.object(PluginsManager, "check_payment_balance")
@patch.object(PaymentCheckBalance, "validate_gateway")
@patch.object(PaymentCheckBalance, "validate_currency")
def test_payment_check_balance_validate_channel_does_not_exist(
    _, __, check_payment_balance_mock, staff_api_client, check_payment_balance_input
):
    check_payment_balance_input["channel"] = "not_existing_channel"
    response = staff_api_client.post_graphql(
        MUTATION_CHECK_PAYMENT_BALANCE, {"input": check_payment_balance_input}
    )

    content = get_graphql_content(response)
    errors = content["data"]["paymentCheckBalance"]["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == PaymentErrorCode.NOT_FOUND.value.upper()
    assert errors[0]["field"] == "channel"
    assert errors[0]["message"] == (
        "Channel with 'not_existing_channel' slug does not exist."
    )

    assert check_payment_balance_mock.call_count == 0


@patch.object(PluginsManager, "check_payment_balance")
@patch.object(PaymentCheckBalance, "validate_gateway")
@patch.object(PaymentCheckBalance, "validate_currency")
def test_payment_check_balance_validate_channel_inactive(
    _,
    __,
    check_payment_balance_mock,
    staff_api_client,
    channel_USD,
    check_payment_balance_input,
):
    channel_USD.is_active = False
    channel_USD.save(update_fields=["is_active"])
    check_payment_balance_input["channel"] = "main"

    response = staff_api_client.post_graphql(
        MUTATION_CHECK_PAYMENT_BALANCE, {"input": check_payment_balance_input}
    )

    content = get_graphql_content(response)
    errors = content["data"]["paymentCheckBalance"]["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == PaymentErrorCode.CHANNEL_INACTIVE.value.upper()
    assert errors[0]["field"] == "channel"
    assert errors[0]["message"] == "Channel with 'main' is inactive."
    assert check_payment_balance_mock.call_count == 0


@patch.object(PluginsManager, "check_payment_balance")
@patch.object(PaymentCheckBalance, "validate_gateway")
@patch.object(PaymentCheckBalance, "validate_currency")
@patch("saleor.graphql.payment.mutations.validate_channel")
def test_payment_check_balance_payment(
    _,
    __,
    ___,
    check_payment_balance_mock,
    staff_api_client,
    check_payment_balance_input,
):
    staff_api_client.post_graphql(
        MUTATION_CHECK_PAYMENT_BALANCE, {"input": check_payment_balance_input}
    )

    check_payment_balance_mock.assert_called_once_with(
        {
            "gateway_id": "mirumee.payments.gateway",
            "method": "givex",
            "card": {
                "cvc": "9891",
                "code": "12345678910",
                "money": {"currency": "GBP", "amount": 100.0},
            },
        },
        "channel_default",
    )


@patch.object(PluginsManager, "check_payment_balance")
@patch.object(PaymentCheckBalance, "validate_gateway")
@patch.object(PaymentCheckBalance, "validate_currency")
@patch("saleor.graphql.payment.mutations.validate_channel")
def test_payment_check_balance_balance_raises_error(
    _,
    __,
    ___,
    check_payment_balance_mock,
    staff_api_client,
    check_payment_balance_input,
):
    check_payment_balance_mock.side_effect = Mock(
        side_effect=PaymentError("Test payment error")
    )

    response = staff_api_client.post_graphql(
        MUTATION_CHECK_PAYMENT_BALANCE, {"input": check_payment_balance_input}
    )

    content = get_graphql_content(response)
    errors = content["data"]["paymentCheckBalance"]["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == PaymentErrorCode.BALANCE_CHECK_ERROR.value.upper()
    assert errors[0]["message"] == "Test payment error"

    check_payment_balance_mock.assert_called_once_with(
        {
            "gateway_id": "mirumee.payments.gateway",
            "method": "givex",
            "card": {
                "cvc": "9891",
                "code": "12345678910",
                "money": {"currency": "GBP", "amount": 100.0},
            },
        },
        "channel_default",
    )
