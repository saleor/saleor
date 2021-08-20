from unittest.mock import patch

from graphql_relay.node.node import to_global_id

from ....account.models import User
from ....core.notify_events import UserNotifyEvent


@patch("saleor.plugins.manager.PluginsManager.notify_in_single_plugin")
def test_notify_sendgrid_via_external_notification_trigger_for_sendgrid_plugin(
    notify_single_plugin_mock,
    settings,
    staff_users,
    external_notification_trigger_query,
    staff_api_client,
    permission_manage_users,
    sendgrid_email_plugin,
):

    settings.PLUGINS = [
        "saleor.plugins.sendgrid.plugin.SendgridEmailPlugin",
    ]
    sendgrid_email_plugin(active=True, api_key="AB12")
    test_template_id = "2efac70d-64ed-4e57-9951-f87e14d7e60e"

    variables = {
        "input": {
            "ids": [to_global_id(User.__name__, user.id) for user in staff_users],
            "extraPayload": '{"recipient_email":"test@gmail.com"}',
            "externalEventType": test_template_id,
        },
        "pluginId": "mirumee.notifications.sendgrid_email",
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[permission_manage_users],
    )

    assert response.status_code == 200
    assert notify_single_plugin_mock.call_count == 3


def test_notification_trigger_for_all_plugins_logs_checking(
    settings,
    staff_users,
    external_notification_trigger_query,
    staff_api_client,
    permission_manage_users,
    caplog,
):

    settings.PLUGINS = [
        "saleor.plugins.user_email.plugin.UserEmailPlugin",
        "saleor.plugins.sendgrid.plugin.SendgridEmailPlugin",
        "saleor.plugins.webhook.plugin.WebhookPlugin",
        "saleor.plugins.admin_email.plugin.AdminEmailPlugin",
    ]

    test_template_id = "2efac70d-64ed-4e57-9951-f87e14d7e60e"

    variables = {
        "input": {
            "ids": [to_global_id(User.__name__, user.id) for user in staff_users],
            "extraPayload": '{"recipient_email":"test@gmail.com"}',
            "externalEventType": test_template_id,
        },
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[permission_manage_users],
    )

    assert response.status_code == 200
    assert (
        f"Webhook notify_user triggered for {test_template_id} notify event."
        in caplog.text
    )


def test_notify_sendgrid_via_external_notification_trigger_for_all_plugins_lack_of_logs(
    settings,
    staff_users,
    external_notification_trigger_query,
    staff_api_client,
    permission_manage_users,
    caplog,
):

    settings.PLUGINS = [
        "saleor.plugins.user_email.plugin.UserEmailPlugin",
        "saleor.plugins.sendgrid.plugin.SendgridEmailPlugin",
        "saleor.plugins.webhook.plugin.WebhookPlugin",
        "saleor.plugins.admin_email.plugin.AdminEmailPlugin",
    ]

    test_template_id = "2efac70d-64ed-4e57-9951-f87e14d7e60e"

    variables = {
        "input": {
            "ids": [to_global_id(User.__name__, user.id) for user in staff_users],
            "extraPayload": '{"recipient_email":"test@gmail.com"}',
            "externalEventType": UserNotifyEvent.ORDER_CANCELED,
        },
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[permission_manage_users],
    )

    assert response.status_code == 200
    assert (
        f"Webhook notify_user triggered for {test_template_id} notify event."
        not in caplog.text
    )
    assert (
        f"Send email with event {test_template_id} as dynamic template ID."
        not in caplog.text
    )
