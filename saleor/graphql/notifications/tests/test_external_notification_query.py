import json
from unittest.mock import patch

import pytest
from graphql_relay.node.node import to_global_id

from ....account.models import User
from ....core.notify_events import UserNotifyEvent
from ....graphql.tests.utils import assert_no_permission
from ....plugins.tests.sample_plugins import PluginSample

query_test_invalid_data = [
    (
        {
            "input": {
                "ids": [],
                "extraPayload": json.dumps("{}"),
                "externalEventType": {},
            }
        },
        400,
        'Argument "channel" of required type String!" provided the variable '
        '"$channel" which was not provided',
    ),
    (
        {
            "input": {
                "extraPayload": json.dumps("{}"),
                "externalEventType": {},
            },
            "channel": "c-pln",
        },
        400,
        'Variable "$input" got invalid value {"externalEventType": {},'
        ' "extraPayload": "\\"{}\\""}.\nIn field "ids": Expected "[ID!]!", found null.',
    ),
    (
        {
            "input": {
                "ids": [],
                "extraPayload": json.dumps("{}"),
            },
            "channel": "c-pln",
        },
        400,
        'Variable "$input" got invalid value {"extraPayload": "\\"{}\\"",'
        ' "ids": []}.\nIn field "externalEventType": Expected "String!", found null.',
    ),
]


@pytest.mark.parametrize("variables, status_code, message", query_test_invalid_data)
def test_external_notification_trigger_query_with_invalid_data(
    variables,
    status_code,
    message,
    external_notification_trigger_query,
    staff_api_client,
    permission_manage_users,
    channel_PLN,
):
    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[permission_manage_users],
        check_no_permissions=False,
    )
    assert response.status_code == status_code
    json_response = response.json()
    errors = json_response["errors"]
    assert len(errors) == 1
    assert errors[0]["message"] == message


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_notify_via_external_notification_trigger_for_plugin_manager(
    plugin_manager_notify_mock,
    settings,
    staff_users,
    external_notification_trigger_query,
    staff_api_client,
    permission_manage_users,
    channel_PLN,
):

    settings.PLUGINS = ["saleor.plugins.tests.sample_plugins.PluginSample"]

    variables = {
        "input": {
            "ids": [to_global_id(User.__name__, user.id) for user in staff_users],
            "extraPayload": "{}",
            "externalEventType": UserNotifyEvent.ORDER_CANCELED,
        },
        "channel": channel_PLN.slug,
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[permission_manage_users],
    )

    assert response.status_code == 200
    assert plugin_manager_notify_mock.call_count == 3
    assert len(response.json()["data"]["externalNotificationTrigger"]["errors"]) == 0


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_notify_via_external_notification_trigger_without_permission(
    plugin_manager_notify_mock,
    staff_users,
    external_notification_trigger_query,
    staff_api_client,
    channel_PLN,
):

    variables = {
        "input": {
            "ids": [to_global_id(User.__name__, user.id) for user in staff_users],
            "extraPayload": "{}",
            "externalEventType": UserNotifyEvent.ORDER_CANCELED,
        },
        "channel": channel_PLN.slug,
        "pluginId": PluginSample.PLUGIN_ID,
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query, variables
    )
    assert_no_permission(response)
    plugin_manager_notify_mock.assert_not_called()
