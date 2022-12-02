from unittest.mock import patch

from graphql_relay.node.node import to_global_id

from ....account.models import User


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_notify_via_external_notification_trigger(
    notify_single_plugin_mock,
    settings,
    staff_users,
    external_notification_trigger_query,
    staff_api_client,
    permission_manage_users,
    channel_PLN,
):

    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
    ]
    test_template_id = "2efac70d-64ed-4e57-9951-f87e14d7e60e"

    variables = {
        "input": {
            "ids": [to_global_id(User.__name__, user.id) for user in staff_users],
            "extraPayload": '{"recipient_email":"test@gmail.com"}',
            "externalEventType": test_template_id,
        },
        "pluginId": "mirumee.notifications.sendgrid_email",
        "channel": channel_PLN.slug,
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[permission_manage_users],
    )

    assert response.status_code == 200
    assert notify_single_plugin_mock.call_count == 3
