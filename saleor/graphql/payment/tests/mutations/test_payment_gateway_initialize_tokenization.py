from unittest.mock import patch

import pytest

from .....payment.interface import (
    PaymentGatewayInitializeTokenizationRequestData,
    PaymentGatewayInitializeTokenizationResponseData,
    PaymentGatewayInitializeTokenizationResult,
)
from .....plugins.manager import PluginsManager
from ....core.enums import PaymentGatewayInitializeTokenizationErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import PaymentGatewayInitializeTokenizationResultEnum

PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION = """
mutation PaymentGatewayInitializeTokenization(
$id: String!, $channel: String!, $data: JSON){
  paymentGatewayInitializeTokenization(id: $id, channel: $channel, data: $data){
    result
    data
    errors{
      field
      code
      message
    }
  }
}
"""


@pytest.mark.parametrize(
    "expected_input_data, expected_output_data",
    [
        (None, None),
        (None, {"foo": "bar1"}),
        ({"foo": "bar2"}, None),
        ({"foo": "bar3"}, {"foo": "bar4"}),
    ],
)
@patch.object(PluginsManager, "payment_gateway_initialize_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_gateway_initialize_tokenization(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_gateway_initialize_tokenization,
    expected_input_data,
    expected_output_data,
    user_api_client,
    channel_USD,
):
    # given
    mocked_is_event_active_for_any_plugin.return_value = True
    mocked_payment_gateway_initialize_tokenization.return_value = (
        PaymentGatewayInitializeTokenizationResponseData(
            result=PaymentGatewayInitializeTokenizationResult.SUCCESSFULLY_INITIALIZED,
            error=None,
            data=expected_output_data,
        )
    )
    expected_id = "test_id"

    # when
    response = user_api_client.post_graphql(
        PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION,
        variables={
            "id": expected_id,
            "channel": channel_USD.slug,
            "data": expected_input_data,
        },
    )

    # then
    content = get_graphql_content(response)
    response_data = content["data"]["paymentGatewayInitializeTokenization"]
    assert response_data["result"] == (
        PaymentGatewayInitializeTokenizationResultEnum.SUCCESSFULLY_INITIALIZED.name
    )
    assert response_data["data"] == expected_output_data

    mocked_is_event_active_for_any_plugin.assert_called_once_with(
        "payment_gateway_initialize_tokenization"
    )
    mocked_payment_gateway_initialize_tokenization.assert_called_once_with(
        request_data=PaymentGatewayInitializeTokenizationRequestData(
            user=user_api_client.user,
            channel=channel_USD,
            app_identifier=expected_id,
            data=expected_input_data,
        )
    )


@patch.object(PluginsManager, "payment_gateway_initialize_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_gateway_initialize_tokenization_called_by_anonymous_user(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_gateway_initialize_tokenization,
    api_client,
    channel_USD,
):
    # given
    expected_id = "test_id"

    # when
    response = api_client.post_graphql(
        PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION,
        variables={"id": expected_id, "channel": channel_USD.slug},
    )

    # then
    assert_no_permission(response)

    assert not mocked_is_event_active_for_any_plugin.called
    assert not mocked_payment_gateway_initialize_tokenization.called


@patch.object(PluginsManager, "payment_gateway_initialize_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_gateway_initialize_tokenization_called_by_app(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_gateway_initialize_tokenization,
    app_api_client,
    channel_USD,
):
    # given
    expected_id = "test_id"

    # when
    response = app_api_client.post_graphql(
        PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION,
        variables={"id": expected_id, "channel": channel_USD.slug},
    )

    # then
    assert_no_permission(response)

    assert not mocked_is_event_active_for_any_plugin.called
    assert not mocked_payment_gateway_initialize_tokenization.called


@patch.object(PluginsManager, "payment_gateway_initialize_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_gateway_initialize_tokenization_not_app_or_plugin_subscribed_to_event(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_gateway_initialize_tokenization,
    user_api_client,
    channel_USD,
):
    # given
    mocked_is_event_active_for_any_plugin.return_value = False

    expected_id = "test_id"

    # when
    response = user_api_client.post_graphql(
        PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION,
        variables={"id": expected_id, "channel": channel_USD.slug},
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["paymentGatewayInitializeTokenization"]["errors"]) == 1
    assert (
        content["data"]["paymentGatewayInitializeTokenization"]["errors"][0]["code"]
        == PaymentGatewayInitializeTokenizationErrorCode.NOT_FOUND.name
    )
    assert content["data"]["paymentGatewayInitializeTokenization"]["result"] == (
        PaymentGatewayInitializeTokenizationResultEnum.FAILED_TO_DELIVER.name
    )

    mocked_is_event_active_for_any_plugin.assert_called_once_with(
        "payment_gateway_initialize_tokenization"
    )
    assert not mocked_payment_gateway_initialize_tokenization.called


@patch.object(PluginsManager, "payment_gateway_initialize_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_gateway_initialize_tokenization_incorrect_channel(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_gateway_initialize_tokenization,
    user_api_client,
):
    # given
    expected_id = "test_id"

    # when
    response = user_api_client.post_graphql(
        PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION,
        variables={"id": expected_id, "channel": "non-exiting-channel"},
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["paymentGatewayInitializeTokenization"]["errors"]) == 1
    assert (
        content["data"]["paymentGatewayInitializeTokenization"]["errors"][0]["code"]
        == PaymentGatewayInitializeTokenizationErrorCode.NOT_FOUND.name
    )
    assert content["data"]["paymentGatewayInitializeTokenization"]["result"] == (
        PaymentGatewayInitializeTokenizationResultEnum.FAILED_TO_DELIVER.name
    )

    assert not mocked_is_event_active_for_any_plugin.called
    assert not mocked_payment_gateway_initialize_tokenization.called


@patch.object(PluginsManager, "payment_gateway_initialize_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_gateway_initialize_tokenization_failure_from_app(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_gateway_initialize_tokenization,
    user_api_client,
    channel_USD,
):
    # given
    error_message = "Error message"
    mocked_is_event_active_for_any_plugin.return_value = True
    mocked_payment_gateway_initialize_tokenization.return_value = (
        PaymentGatewayInitializeTokenizationResponseData(
            result=PaymentGatewayInitializeTokenizationResult.FAILED_TO_INITIALIZE,
            error=error_message,
            data=None,
        )
    )
    expected_id = "test_id"

    # when
    response = user_api_client.post_graphql(
        PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION,
        variables={
            "id": expected_id,
            "channel": channel_USD.slug,
            "data": None,
        },
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["paymentGatewayInitializeTokenization"]["result"] == (
        PaymentGatewayInitializeTokenizationResultEnum.FAILED_TO_INITIALIZE.name
    )
    assert len(content["data"]["paymentGatewayInitializeTokenization"]["errors"]) == 1
    error = content["data"]["paymentGatewayInitializeTokenization"]["errors"][0]
    assert (
        error["code"]
        == PaymentGatewayInitializeTokenizationErrorCode.GATEWAY_ERROR.name
    )
    assert error["message"] == error_message

    mocked_is_event_active_for_any_plugin.assert_called_once_with(
        "payment_gateway_initialize_tokenization"
    )
    mocked_payment_gateway_initialize_tokenization.assert_called_once_with(
        request_data=PaymentGatewayInitializeTokenizationRequestData(
            user=user_api_client.user,
            channel=channel_USD,
            app_identifier=expected_id,
            data=None,
        )
    )
