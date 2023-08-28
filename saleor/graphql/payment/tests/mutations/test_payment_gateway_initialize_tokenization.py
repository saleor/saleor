from unittest.mock import patch

import pytest

from .....payment.interface import (
    PaymentGatewayInitializeTokenizationRequestData,
    PaymentGatewayInitializeTokenizationResponseData,
)
from .....plugins.manager import PluginsManager
from ....core.enums import PaymentGatewayInitializeTokenizationErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content

PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION = """
mutation PaymentGatewayInitializeTokenization(
$id: String!, $channel: String!, $data: JSON){
  paymentGatewayInitializeTokenization(id: $id, channel: $channel, data: $data){
    success
    message
    data
    errors{
      field
      code
    }
  }
}
"""


@pytest.mark.parametrize("expected_data", [None, {"foo": "bar"}])
@patch.object(PluginsManager, "payment_gateway_initialize_tokenization")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_payment_gateway_initialize_tokenization(
    mocked_is_event_active_for_any_plugin,
    mocked_payment_gateway_initialize_tokenization,
    expected_data,
    user_api_client,
    channel_USD,
):
    # given
    mocked_is_event_active_for_any_plugin.return_value = True
    mocked_payment_gateway_initialize_tokenization.return_value = (
        PaymentGatewayInitializeTokenizationResponseData(
            success=True,
            message=None,
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
            "data": expected_data,
        },
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["paymentGatewayInitializeTokenization"]["success"] is True

    mocked_is_event_active_for_any_plugin.assert_called_once_with(
        "payment_gateway_initialize_tokenization"
    )
    mocked_payment_gateway_initialize_tokenization.assert_called_once_with(
        request_data=PaymentGatewayInitializeTokenizationRequestData(
            user=user_api_client.user,
            channel=channel_USD,
            app_identifier=expected_id,
            data=expected_data,
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
    mocked_is_event_active_for_any_plugin.return_value = True
    mocked_payment_gateway_initialize_tokenization.return_value = (
        PaymentGatewayInitializeTokenizationResponseData(
            success=True,
            message=None,
            data=None,
        )
    )
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
    mocked_is_event_active_for_any_plugin.return_value = True
    mocked_payment_gateway_initialize_tokenization.return_value = (
        PaymentGatewayInitializeTokenizationResponseData(
            success=True,
            message=None,
            data=None,
        )
    )
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
    mocked_payment_gateway_initialize_tokenization.return_value = (
        PaymentGatewayInitializeTokenizationResponseData(
            success=True,
            message=None,
            data=None,
        )
    )
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
    mocked_is_event_active_for_any_plugin.return_value = False
    mocked_payment_gateway_initialize_tokenization.return_value = (
        PaymentGatewayInitializeTokenizationResponseData(
            success=True,
            message=None,
            data=None,
        )
    )
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

    assert not mocked_is_event_active_for_any_plugin.called
    assert not mocked_payment_gateway_initialize_tokenization.called
