from unittest.mock import patch

import pytest

from .....payment.interface import (
    PaymentMethodProcessTokenizationRequestData,
    PaymentMethodTokenizationResponseData,
    PaymentMethodTokenizationResult,
)
from .....plugins.manager import PluginsManager
from ....core.enums import PaymentMethodProcessTokenizationErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import PaymentMethodTokenizationResultEnum

PAYMENT_METHOD_PROCESS_TOKENIZATION = """
mutation PaymentMethodProcessTokenization(
$id: String!, $channel: String!, $data: JSON){
  paymentMethodProcessTokenization(id: $id, channel: $channel, data: $data){
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
    "expected_input_data, expected_output_data",
    [
        (None, None),
        (None, {"foo": "bar1"}),
        ({"foo": "bar2"}, None),
        ({"foo": "bar3"}, {"foo": "bar4"}),
    ],
)
@patch.object(PluginsManager, "payment_method_process_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_method_process_tokenization(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_method_process_tokenization,
    expected_input_data,
    expected_output_data,
    user_api_client,
    channel_USD,
    app,
):
    # given
    expected_payment_method_id = "test_id"
    mocked_is_event_active_for_any_plugin.return_value = True
    mocked_payment_method_process_tokenization.return_value = (
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
        PAYMENT_METHOD_PROCESS_TOKENIZATION,
        variables={
            "id": expected_id,
            "channel": channel_USD.slug,
            "data": expected_input_data,
        },
    )

    # then
    content = get_graphql_content(response)

    response_data = content["data"]["paymentMethodProcessTokenization"]
    assert response_data["result"] == (
        PaymentMethodTokenizationResultEnum.SUCCESSFULLY_TOKENIZED.name
    )
    assert response_data["data"] == expected_output_data
    assert response_data["id"] == expected_payment_method_id
    mocked_is_event_active_for_any_plugin.assert_called_once_with(
        "payment_method_process_tokenization"
    )
    mocked_payment_method_process_tokenization.assert_called_once_with(
        request_data=PaymentMethodProcessTokenizationRequestData(
            user=user_api_client.user,
            channel=channel_USD,
            id=expected_id,
            data=expected_input_data,
        )
    )


@patch.object(PluginsManager, "payment_method_process_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_method_process_tokenization_called_by_anonymous_user(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_method_process_tokenization,
    api_client,
    channel_USD,
    app,
):
    # given
    expected_id = "test_id"

    # when
    response = api_client.post_graphql(
        PAYMENT_METHOD_PROCESS_TOKENIZATION,
        variables={"id": expected_id, "channel": channel_USD.slug},
    )

    # then
    assert_no_permission(response)

    assert not mocked_is_event_active_for_any_plugin.called
    assert not mocked_payment_method_process_tokenization.called


@patch.object(PluginsManager, "payment_method_process_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_method_process_tokenization_called_by_app(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_method_process_tokenization,
    app_api_client,
    channel_USD,
    app,
):
    # given
    expected_id = "test_id"

    # when
    response = app_api_client.post_graphql(
        PAYMENT_METHOD_PROCESS_TOKENIZATION,
        variables={"id": expected_id, "channel": channel_USD.slug},
    )

    # then
    assert_no_permission(response)

    assert not mocked_is_event_active_for_any_plugin.called
    assert not mocked_payment_method_process_tokenization.called


@patch.object(PluginsManager, "payment_method_process_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_method_process_tokenization_not_app_or_plugin_subscribed_to_event(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_method_process_tokenization,
    user_api_client,
    channel_USD,
    app,
):
    # given
    mocked_is_event_active_for_any_plugin.return_value = False

    expected_id = "test_id"

    # when
    response = user_api_client.post_graphql(
        PAYMENT_METHOD_PROCESS_TOKENIZATION,
        variables={"id": expected_id, "channel": channel_USD.slug},
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["paymentMethodProcessTokenization"]["errors"]) == 1
    assert (
        content["data"]["paymentMethodProcessTokenization"]["errors"][0]["code"]
        == PaymentMethodProcessTokenizationErrorCode.NOT_FOUND.name
    )
    assert content["data"]["paymentMethodProcessTokenization"]["result"] == (
        PaymentMethodTokenizationResultEnum.FAILED_TO_DELIVER.name
    )

    mocked_is_event_active_for_any_plugin.assert_called_once_with(
        "payment_method_process_tokenization"
    )
    assert not mocked_payment_method_process_tokenization.called


@patch.object(PluginsManager, "payment_method_process_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_method_process_tokenization_incorrect_channel(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_method_process_tokenization,
    user_api_client,
    app,
):
    # given
    expected_id = "test_id"

    # when
    response = user_api_client.post_graphql(
        PAYMENT_METHOD_PROCESS_TOKENIZATION,
        variables={"id": expected_id, "channel": "non-exiting-channel"},
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["paymentMethodProcessTokenization"]["errors"]) == 1
    assert (
        content["data"]["paymentMethodProcessTokenization"]["errors"][0]["code"]
        == PaymentMethodProcessTokenizationErrorCode.NOT_FOUND.name
    )
    assert content["data"]["paymentMethodProcessTokenization"]["result"] == (
        PaymentMethodTokenizationResultEnum.FAILED_TO_DELIVER.name
    )

    assert not mocked_is_event_active_for_any_plugin.called
    assert not mocked_payment_method_process_tokenization.called


@patch.object(PluginsManager, "payment_method_process_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_method_process_tokenization_failure_from_app(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_method_process_tokenization,
    user_api_client,
    channel_USD,
    app,
):
    # given
    error_message = "Error message"
    mocked_is_event_active_for_any_plugin.return_value = True
    mocked_payment_method_process_tokenization.return_value = (
        PaymentMethodTokenizationResponseData(
            result=PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE,
            error=error_message,
            data=None,
        )
    )
    expected_id = "test_id"

    # when
    response = user_api_client.post_graphql(
        PAYMENT_METHOD_PROCESS_TOKENIZATION,
        variables={
            "id": expected_id,
            "channel": channel_USD.slug,
            "data": None,
        },
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["paymentMethodProcessTokenization"]["result"] == (
        PaymentMethodTokenizationResultEnum.FAILED_TO_TOKENIZE.name
    )
    assert len(content["data"]["paymentMethodProcessTokenization"]["errors"]) == 1
    error = content["data"]["paymentMethodProcessTokenization"]["errors"][0]
    assert error["code"] == PaymentMethodProcessTokenizationErrorCode.GATEWAY_ERROR.name
    assert error["message"] == error_message

    mocked_is_event_active_for_any_plugin.assert_called_once_with(
        "payment_method_process_tokenization"
    )
    mocked_payment_method_process_tokenization.assert_called_once_with(
        request_data=PaymentMethodProcessTokenizationRequestData(
            user=user_api_client.user,
            channel=channel_USD,
            id=expected_id,
            data=None,
        )
    )
