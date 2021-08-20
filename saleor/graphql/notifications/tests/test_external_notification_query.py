import json
from unittest.mock import patch

import pytest
from graphql_relay.node.node import to_global_id

from ....account.models import User
from ....core.notify_events import UserNotifyEvent
from ....graphql.tests.utils import assert_no_permission
from ....webhook.payloads import generate_customer_payload

query_test_data = [
    (
        {
            "input": {
                "ids": [],
                "extraPayload": json.dumps("{}"),
                "externalEventType": {},
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
            }
        },
        200,
    ),
    (
        {"input": {"extraPayload": json.dumps("{}"), "externalEventType": {}}},
        400,
    ),
    ({"input": {"ids": [], "externalEventType": {}}}, 200),
    (
        {
            "input": {
                "ids": [],
                "extraPayload": json.dumps("{}"),
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
):
    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[permission_manage_users],
        check_no_permissions=False,
    )
    assert response.status_code == status_code


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_notify_sendgrid_via_external_notification_trigger_for_all_plugins(
    plugin_manager_notify_mock,
    settings,
    staff_users,
    external_notification_trigger_query,
    staff_api_client,
    permission_manage_users,
    sendgrid_email_plugin,
):
    sendgrid_email_plugin(active=True, api_key="AB12")

    settings.PLUGINS = [
        "saleor.plugins.user_email.plugin.UserEmailPlugin",
        "saleor.plugins.sendgrid.plugin.SendgridEmailPlugin",
        "saleor.plugins.webhook.plugin.WebhookPlugin",
        "saleor.plugins.admin_email.plugin.AdminEmailPlugin",
    ]

    variables = {
        "input": {
            "ids": [to_global_id(User.__name__, user.id) for user in staff_users],
            "extraPayload": "{}",
            "externalEventType": UserNotifyEvent.ORDER_CANCELED,
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
    sendgrid_email_plugin,
    external_notification_trigger_query,
    staff_api_client,
):
    plugin = sendgrid_email_plugin(
        active=True, api_key="AB12", account_password_reset_template_id="123"
    )
    variables = {
        "input": {
            "ids": [to_global_id(User.__name__, user.id) for user in staff_users],
            "extraPayload": "{}",
            "externalEventType": UserNotifyEvent.ORDER_CANCELED,
        },
        "pluginId": plugin.PLUGIN_ID,
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query, variables
    )
    assert_no_permission(response)
    assert response.status_code == 200
    plugin_manager_notify_mock.assert_not_called()


@patch("saleor.plugins.sendgrid.plugin.SendgridEmailPlugin.notify")
def test_notify_via_external_notification_trigger_with_extra_payload(
    sendgrid_plugin_notify,
    staff_users,
    sendgrid_email_plugin,
    external_notification_trigger_query,
    staff_api_client,
    permission_manage_users,
):

    test_json = {"TEST": "VALUE", "TEST_LIST": ["GUEST1", "GUEST2"]}
    plugin = sendgrid_email_plugin(
        active=True, api_key="AB12", account_password_reset_template_id="123"
    )
    variables = {
        "input": {
            "ids": [to_global_id(User.__name__, user.id) for user in staff_users],
            "extraPayload": json.dumps(test_json),
            "externalEventType": UserNotifyEvent.ORDER_CANCELED,
        },
        "pluginId": plugin.PLUGIN_ID,
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[permission_manage_users],
    )

    expected_payload = [
        json.loads(generate_customer_payload(user)) for user in staff_users
    ]
    for payload in expected_payload:
        payload[0]["extra_payload"] = test_json
    assert response.status_code == 200
    assert sendgrid_plugin_notify.call_count == 3
    sendgrid_plugin_notify.assert_called_with(
        event=UserNotifyEvent.ORDER_CANCELED,
        payload=expected_payload[0][0],
        previous_value=None,
    )
