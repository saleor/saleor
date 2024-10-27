from unittest.mock import patch

from .....payment.interface import (
    StoredPaymentMethodRequestDeleteData,
    StoredPaymentMethodRequestDeleteResponseData,
    StoredPaymentMethodRequestDeleteResult,
)
from .....plugins.manager import PluginsManager
from ....core.enums import StoredPaymentMethodRequestDeleteErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import StoredPaymentMethodRequestDeleteResultEnum

STORED_PAYMENT_METHOD_REQUEST_DELETE_MUTATION = """
mutation storedPaymentMethodRequestDelete($id: ID!, $channel: String!){
  storedPaymentMethodRequestDelete(id: $id, channel: $channel){
    result
    errors{
      field
      code
      message
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
            result=StoredPaymentMethodRequestDeleteResult.SUCCESSFULLY_DELETED.value,
            error=None,
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
    assert (
        content["data"]["storedPaymentMethodRequestDelete"]["result"]
        == StoredPaymentMethodRequestDeleteResultEnum.SUCCESSFULLY_DELETED.name
    )

    mocked_is_event_active_for_any_plugin.assert_called_once_with(
        "stored_payment_method_request_delete", channel_slug=channel_USD.slug
    )
    mocked_stored_payment_method_request_delete.assert_called_once_with(
        request_delete_data=StoredPaymentMethodRequestDeleteData(
            payment_method_id=expected_id,
            user=user_api_client.user,
            channel=channel_USD,
        ),
    )


@patch.object(PluginsManager, "stored_payment_method_request_delete")
@patch.object(PluginsManager, "is_event_active_for_any_plugin")
def test_stored_payment_method_request_delete_app_returned_failure_event(
    mocked_is_event_active_for_any_plugin,
    mocked_stored_payment_method_request_delete,
    user_api_client,
    channel_USD,
):
    # given
    expected_error_message = "Failed to delete"
    mocked_is_event_active_for_any_plugin.return_value = True
    mocked_stored_payment_method_request_delete.return_value = (
        StoredPaymentMethodRequestDeleteResponseData(
            result=StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELETE.value,
            error=expected_error_message,
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
    assert (
        content["data"]["storedPaymentMethodRequestDelete"]["result"]
        == StoredPaymentMethodRequestDeleteResultEnum.FAILED_TO_DELETE.name
    )
    assert len(content["data"]["storedPaymentMethodRequestDelete"]["errors"]) == 1
    error = content["data"]["storedPaymentMethodRequestDelete"]["errors"][0]
    assert error["code"] == StoredPaymentMethodRequestDeleteErrorCode.GATEWAY_ERROR.name
    assert error["message"] == expected_error_message

    mocked_is_event_active_for_any_plugin.assert_called_once_with(
        "stored_payment_method_request_delete", channel_slug=channel_USD.slug
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
            result=StoredPaymentMethodRequestDeleteResult.SUCCESSFULLY_DELETED.value,
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
def test_stored_payment_method_request_delete_called_by_anonymous_user(
    mocked_is_event_active_for_any_plugin,
    mocked_stored_payment_method_request_delete,
    api_client,
    channel_USD,
):
    # given
    mocked_is_event_active_for_any_plugin.return_value = True
    mocked_stored_payment_method_request_delete.return_value = (
        StoredPaymentMethodRequestDeleteResponseData(
            result=StoredPaymentMethodRequestDeleteResult.SUCCESSFULLY_DELETED.value,
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
            result=StoredPaymentMethodRequestDeleteResult.SUCCESSFULLY_DELETED.value,
            error=None,
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
    assert (
        content["data"]["storedPaymentMethodRequestDelete"]["result"]
        == StoredPaymentMethodRequestDeleteResultEnum.FAILED_TO_DELIVER.name
    )
    assert len(content["data"]["storedPaymentMethodRequestDelete"]["errors"]) == 1
    assert (
        content["data"]["storedPaymentMethodRequestDelete"]["errors"][0]["code"]
        == StoredPaymentMethodRequestDeleteErrorCode.NOT_FOUND.name
    )

    mocked_is_event_active_for_any_plugin.assert_called_once_with(
        "stored_payment_method_request_delete", channel_slug=channel_USD.slug
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
            result=StoredPaymentMethodRequestDeleteResult.SUCCESSFULLY_DELETED,
            error=None,
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
    assert (
        content["data"]["storedPaymentMethodRequestDelete"]["result"]
        == StoredPaymentMethodRequestDeleteResultEnum.FAILED_TO_DELIVER.name
    )

    assert not mocked_is_event_active_for_any_plugin.called
    assert not mocked_stored_payment_method_request_delete.called
