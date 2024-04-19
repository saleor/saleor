from unittest.mock import patch

import pytest

from .....payment import TokenizedPaymentFlow
from .....payment.interface import (
    PaymentMethodInitializeTokenizationRequestData,
    PaymentMethodTokenizationResponseData,
    PaymentMethodTokenizationResult,
)
from .....plugins.manager import PluginsManager
from .....webhook.transport.utils import to_payment_app_id
from ....core.enums import PaymentMethodInitializeTokenizationErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import PaymentMethodTokenizationResultEnum, TokenizedPaymentFlowEnum

PAYMENT_METHOD_INITIALIZE_TOKENIZATION = """
mutation PaymentMethodInitializeTokenization(
$id: String!, $channel: String!, $data: JSON,
$paymentFlowToSupport: TokenizedPaymentFlowEnum!){
  paymentMethodInitializeTokenization(
    id: $id, channel: $channel, data: $data, paymentFlowToSupport: $paymentFlowToSupport
  ){
    result
    data
    id
    errors{
      field
      code
      message
    }
  }
}
"""


@pytest.mark.parametrize(
    ("expected_input_data", "expected_output_data"),
    [
        (None, None),
        (None, {"foo": "bar1"}),
        ({"foo": "bar2"}, None),
        ({"foo": "bar3"}, {"foo": "bar4"}),
    ],
)
@patch.object(PluginsManager, "payment_method_initialize_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_method_initialize_tokenization(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_method_initialize_tokenization,
    expected_input_data,
    expected_output_data,
    user_api_client,
    channel_USD,
    app,
):
    # given
    expected_payment_method_id = to_payment_app_id(app, "test_id")
    mocked_is_event_active_for_any_plugin.return_value = True
    mocked_payment_method_initialize_tokenization.return_value = (
        PaymentMethodTokenizationResponseData(
            result=PaymentMethodTokenizationResult.SUCCESSFULLY_TOKENIZED,
            id=expected_payment_method_id,
            error=None,
            data=expected_output_data,
        )
    )
    expected_id = "test_id"

    # when
    response = user_api_client.post_graphql(
        PAYMENT_METHOD_INITIALIZE_TOKENIZATION,
        variables={
            "id": expected_id,
            "channel": channel_USD.slug,
            "data": expected_input_data,
            "paymentFlowToSupport": TokenizedPaymentFlowEnum.INTERACTIVE.name,
        },
    )

    # then
    content = get_graphql_content(response)
    response_data = content["data"]["paymentMethodInitializeTokenization"]
    assert response_data["result"] == (
        PaymentMethodTokenizationResultEnum.SUCCESSFULLY_TOKENIZED.name
    )
    assert response_data["data"] == expected_output_data
    assert response_data["id"] == expected_payment_method_id
    mocked_is_event_active_for_any_plugin.assert_called_once_with(
        "payment_method_initialize_tokenization", channel_slug=channel_USD.slug
    )
    mocked_payment_method_initialize_tokenization.assert_called_once_with(
        request_data=PaymentMethodInitializeTokenizationRequestData(
            user=user_api_client.user,
            channel=channel_USD,
            app_identifier=expected_id,
            data=expected_input_data,
            payment_flow_to_support=TokenizedPaymentFlow.INTERACTIVE,
        )
    )


@patch.object(PluginsManager, "payment_method_initialize_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_method_initialize_tokenization_called_by_anonymous_user(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_method_initialize_tokenization,
    api_client,
    channel_USD,
):
    # given
    expected_id = "test_id"

    # when
    response = api_client.post_graphql(
        PAYMENT_METHOD_INITIALIZE_TOKENIZATION,
        variables={
            "id": expected_id,
            "channel": channel_USD.slug,
            "paymentFlowToSupport": TokenizedPaymentFlowEnum.INTERACTIVE.name,
        },
    )

    # then
    assert_no_permission(response)

    assert not mocked_is_event_active_for_any_plugin.called
    assert not mocked_payment_method_initialize_tokenization.called


@patch.object(PluginsManager, "payment_method_initialize_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_method_initialize_tokenization_called_by_app(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_method_initialize_tokenization,
    app_api_client,
    channel_USD,
):
    # given
    expected_id = "test_id"

    # when
    response = app_api_client.post_graphql(
        PAYMENT_METHOD_INITIALIZE_TOKENIZATION,
        variables={
            "id": expected_id,
            "channel": channel_USD.slug,
            "paymentFlowToSupport": TokenizedPaymentFlowEnum.INTERACTIVE.name,
        },
    )

    # then
    assert_no_permission(response)

    assert not mocked_is_event_active_for_any_plugin.called
    assert not mocked_payment_method_initialize_tokenization.called


@patch.object(PluginsManager, "payment_method_initialize_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_method_initialize_tokenization_not_app_or_plugin_subscribed_to_event(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_method_initialize_tokenization,
    user_api_client,
    channel_USD,
):
    # given
    mocked_is_event_active_for_any_plugin.return_value = False

    expected_id = "test_id"

    # when
    response = user_api_client.post_graphql(
        PAYMENT_METHOD_INITIALIZE_TOKENIZATION,
        variables={
            "id": expected_id,
            "channel": channel_USD.slug,
            "paymentFlowToSupport": TokenizedPaymentFlowEnum.INTERACTIVE.name,
        },
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["paymentMethodInitializeTokenization"]["errors"]) == 1
    assert (
        content["data"]["paymentMethodInitializeTokenization"]["errors"][0]["code"]
        == PaymentMethodInitializeTokenizationErrorCode.NOT_FOUND.name
    )
    assert content["data"]["paymentMethodInitializeTokenization"]["result"] == (
        PaymentMethodTokenizationResultEnum.FAILED_TO_DELIVER.name
    )

    mocked_is_event_active_for_any_plugin.assert_called_once_with(
        "payment_method_initialize_tokenization", channel_slug=channel_USD.slug
    )
    assert not mocked_payment_method_initialize_tokenization.called


@patch.object(PluginsManager, "payment_method_initialize_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_method_initialize_tokenization_incorrect_channel(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_method_initialize_tokenization,
    user_api_client,
):
    # given
    expected_id = "test_id"

    # when
    response = user_api_client.post_graphql(
        PAYMENT_METHOD_INITIALIZE_TOKENIZATION,
        variables={
            "id": expected_id,
            "channel": "non-exiting-channel",
            "paymentFlowToSupport": TokenizedPaymentFlowEnum.INTERACTIVE.name,
        },
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["paymentMethodInitializeTokenization"]["errors"]) == 1
    assert (
        content["data"]["paymentMethodInitializeTokenization"]["errors"][0]["code"]
        == PaymentMethodInitializeTokenizationErrorCode.NOT_FOUND.name
    )
    assert content["data"]["paymentMethodInitializeTokenization"]["result"] == (
        PaymentMethodTokenizationResultEnum.FAILED_TO_DELIVER.name
    )

    assert not mocked_is_event_active_for_any_plugin.called
    assert not mocked_payment_method_initialize_tokenization.called


@patch.object(PluginsManager, "payment_method_initialize_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_method_initialize_tokenization_failure_from_app(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_method_initialize_tokenization,
    user_api_client,
    channel_USD,
):
    # given
    error_message = "Error message"
    mocked_is_event_active_for_any_plugin.return_value = True
    mocked_payment_method_initialize_tokenization.return_value = (
        PaymentMethodTokenizationResponseData(
            result=PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE,
            error=error_message,
            data=None,
        )
    )
    expected_id = "test_id"

    # when
    response = user_api_client.post_graphql(
        PAYMENT_METHOD_INITIALIZE_TOKENIZATION,
        variables={
            "id": expected_id,
            "channel": channel_USD.slug,
            "data": None,
            "paymentFlowToSupport": TokenizedPaymentFlowEnum.INTERACTIVE.name,
        },
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["paymentMethodInitializeTokenization"]["result"] == (
        PaymentMethodTokenizationResultEnum.FAILED_TO_TOKENIZE.name
    )
    assert len(content["data"]["paymentMethodInitializeTokenization"]["errors"]) == 1
    error = content["data"]["paymentMethodInitializeTokenization"]["errors"][0]
    assert (
        error["code"] == PaymentMethodInitializeTokenizationErrorCode.GATEWAY_ERROR.name
    )
    assert error["message"] == error_message

    mocked_is_event_active_for_any_plugin.assert_called_once_with(
        "payment_method_initialize_tokenization", channel_slug=channel_USD.slug
    )
    mocked_payment_method_initialize_tokenization.assert_called_once_with(
        request_data=PaymentMethodInitializeTokenizationRequestData(
            user=user_api_client.user,
            channel=channel_USD,
            app_identifier=expected_id,
            data=None,
            payment_flow_to_support=TokenizedPaymentFlow.INTERACTIVE,
        )
    )
