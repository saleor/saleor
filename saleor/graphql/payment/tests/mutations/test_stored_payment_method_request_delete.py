from unittest.mock import patch

from .....payment.interface import (
    StoredPaymentMethodRequestDeleteData,
    StoredPaymentMethodRequestDeleteResponseData,
)
from .....plugins.manager import PluginsManager
from ....core.enums import StoredPaymentMethodRequestDeleteErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content

STORED_PAYMENT_METHOD_REQUEST_DELETE_MUTATION = """
mutation storedPaymentMethodRequestDelete($id: ID!, $channel: String!){
  storedPaymentMethodRequestDelete(id: $id, channel: $channel){
    success
    message
    errors{
      field
      code
    }
  }
}
"""


@patch.object(PluginsManager, "stored_payment_method_request_delete")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_stored_payment_method_request_delete(
    mocked_is_event_active_for_any_plugin,
    mocked_stored_payment_method_request_delete,
    user_api_client,
    channel_USD,
):
    # given
    mocked_is_event_active_for_any_plugin.return_value = True
    mocked_stored_payment_method_request_delete.return_value = (
        StoredPaymentMethodRequestDeleteResponseData(
            success=True,
            message=None,
        )
    )
    expected_id = "test_id"

    # when
    response = user_api_client.post_graphql(
        STORED_PAYMENT_METHOD_REQUEST_DELETE_MUTATION,
        variables={"id": expected_id, "channel": channel_USD.slug},
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["storedPaymentMethodRequestDelete"]["success"] is True

    mocked_is_event_active_for_any_plugin.assert_called_once_with(
        "stored_payment_method_request_delete"
    )
    mocked_stored_payment_method_request_delete.assert_called_once_with(
        request_delete_data=StoredPaymentMethodRequestDeleteData(
            payment_method_id=expected_id,
            user=user_api_client.user,
            channel=channel_USD,
        )
    )


@patch.object(PluginsManager, "stored_payment_method_request_delete")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_stored_payment_method_request_delete_called_by_app(
    mocked_is_event_active_for_any_plugin,
    mocked_stored_payment_method_request_delete,
    app_api_client,
    channel_USD,
):
    # given
    mocked_is_event_active_for_any_plugin.return_value = True
    mocked_stored_payment_method_request_delete.return_value = (
        StoredPaymentMethodRequestDeleteResponseData(
            success=True,
            message="Payment method delete request was processed successfully.",
        )
    )
    expected_id = "test_id"

    # when
    response = app_api_client.post_graphql(
        STORED_PAYMENT_METHOD_REQUEST_DELETE_MUTATION,
        variables={"id": expected_id, "channel": channel_USD.slug},
    )

    # then
    assert_no_permission(response)

    assert not mocked_is_event_active_for_any_plugin.called
    assert not mocked_stored_payment_method_request_delete.called


@patch.object(PluginsManager, "stored_payment_method_request_delete")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_stored_payment_method_request_delete_called_by_anynoums_user(
    mocked_is_event_active_for_any_plugin,
    mocked_stored_payment_method_request_delete,
    api_client,
    channel_USD,
):
    # given
    mocked_is_event_active_for_any_plugin.return_value = True
    mocked_stored_payment_method_request_delete.return_value = (
        StoredPaymentMethodRequestDeleteResponseData(
            success=True,
            message="Payment method delete request was processed successfully.",
        )
    )
    expected_id = "test_id"

    # when
    response = api_client.post_graphql(
        STORED_PAYMENT_METHOD_REQUEST_DELETE_MUTATION,
        variables={"id": expected_id, "channel": channel_USD.slug},
    )

    # then
    assert_no_permission(response)

    assert not mocked_is_event_active_for_any_plugin.called
    assert not mocked_stored_payment_method_request_delete.called


@patch.object(PluginsManager, "stored_payment_method_request_delete")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_stored_payment_method_request_delete_not_app_or_plugin_subscribed_to_event(
    mocked_is_event_active_for_any_plugin,
    mocked_stored_payment_method_request_delete,
    user_api_client,
    channel_USD,
):
    # given
    mocked_is_event_active_for_any_plugin.return_value = False
    mocked_stored_payment_method_request_delete.return_value = (
        StoredPaymentMethodRequestDeleteResponseData(
            success=True,
            message=None,
        )
    )
    expected_id = "test_id"

    # when
    response = user_api_client.post_graphql(
        STORED_PAYMENT_METHOD_REQUEST_DELETE_MUTATION,
        variables={"id": expected_id, "channel": channel_USD.slug},
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["storedPaymentMethodRequestDelete"]["errors"]) == 1
    assert (
        content["data"]["storedPaymentMethodRequestDelete"]["errors"][0]["code"]
        == StoredPaymentMethodRequestDeleteErrorCode.NOT_FOUND.name
    )

    mocked_is_event_active_for_any_plugin.assert_called_once_with(
        "stored_payment_method_request_delete"
    )
    assert not mocked_stored_payment_method_request_delete.called


@patch.object(PluginsManager, "stored_payment_method_request_delete")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_stored_payment_method_request_delete_incorrect_channel(
    mocked_is_event_active_for_any_plugin,
    mocked_stored_payment_method_request_delete,
    user_api_client,
):
    # given
    mocked_is_event_active_for_any_plugin.return_value = False
    mocked_stored_payment_method_request_delete.return_value = (
        StoredPaymentMethodRequestDeleteResponseData(
            success=True,
            message=None,
        )
    )
    expected_id = "test_id"

    # when
    response = user_api_client.post_graphql(
        STORED_PAYMENT_METHOD_REQUEST_DELETE_MUTATION,
        variables={"id": expected_id, "channel": "non-exiting-channel"},
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["storedPaymentMethodRequestDelete"]["errors"]) == 1
    assert (
        content["data"]["storedPaymentMethodRequestDelete"]["errors"][0]["code"]
        == StoredPaymentMethodRequestDeleteErrorCode.NOT_FOUND.name
    )

    assert not mocked_is_event_active_for_any_plugin.called
    assert not mocked_stored_payment_method_request_delete.called
