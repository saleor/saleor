import json
from unittest.mock import patch

import pytest
from graphql_relay.node.node import to_global_id

from ....account.models import User
from ....core.notify_events import UserNotifyEvent
from ....graphql.tests.utils import assert_no_permission
from ....plugins.tests.sample_plugins import PluginSample

query_test_data = [
    (
        {
            "input": {
                "ids": [],
                "extraPayload": json.dumps("{}"),
                "externalEventType": {},
                "channel": "c-pln",
            },
            "pluginId": "",
        },
        200,
    ),
    (
        {
            "input": {
                "ids": [],
                "extraPayload": json.dumps("{}"),
                "externalEventType": {},
                "channel": "c-pln",
            },
            "pluginId": "WRONG-TEST-PLUGIN",
        },
        200,
    ),
    (
        {
            "input": {
                "ids": [],
                "extraPayload": json.dumps("{}"),
                "externalEventType": {},
                "channel": "c-pln",
            }
        },
        200,
    ),
    (
        {
            "input": {
                "ids": [],
                "extraPayload": json.dumps("{}"),
                "externalEventType": {},
            }
        },
        400,
    ),
    (
        {
            "input": {
                "extraPayload": json.dumps("{}"),
                "externalEventType": {},
                "channel": "c-pln",
            }
        },
        400,
    ),
    ({"input": {"ids": [], "externalEventType": {}, "channel": "c-pln"}}, 200),
    (
        {
            "input": {
                "ids": [],
                "extraPayload": json.dumps("{}"),
                "channel": "c-pln",
            }
        },
        400,
    ),
]


@pytest.mark.parametrize("variables, status_code", query_test_data)
def test_query(
    variables,
    status_code,
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


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_notify_via_external_notification_trigger_for_all_plugins(
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
            "channel": channel_PLN.slug,
        }
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[permission_manage_users],
    )

    assert response.status_code == 200
    assert plugin_manager_notify_mock.call_count == 3


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
            "channel": channel_PLN.slug,
        },
        "pluginId": PluginSample.PLUGIN_ID,
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query, variables
    )
    assert_no_permission(response)
    assert response.status_code == 200
    plugin_manager_notify_mock.assert_not_called()
