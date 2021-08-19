import json
from dataclasses import asdict
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ValidationError
from graphql_relay.node.node import to_global_id

from ....account.models import User
from ....core.notify_events import AdminNotifyEvent, UserNotifyEvent
from ....webhook.payloads import generate_product_variant_payload
from ...models import PluginConfiguration
from ..plugin import EVENT_MAP


def test_get_event_map():
    for event in UserNotifyEvent.CHOICES:
        assert event in EVENT_MAP


@patch("sendgrid.base_interface.BaseInterface.send")
def test_send_notification_to_customers_with_product_variant_payload(
    notify_single_plugin_mock,
    settings,
    staff_users,
    staff_api_client,
    permission_manage_users,
    sendgrid_email_plugin,
    product_with_single_variant,
):
    query = """
      mutation ExternalNotificationTrigger(
        $input: ExternalNotificationTriggerInput!
        $pluginId: String
      ) {
          externalNotificationTrigger(
            input: $input,
            pluginId: $pluginId
          ) {
            errors {
              message
            }
          }
      }
    """

    settings.PLUGINS = [
        "saleor.plugins.sendgrid.plugin.SendgridEmailPlugin",
    ]
    sendgrid_email_plugin(active=True, api_key="AB12")
    payload = json.dumps(
        json.loads(
            generate_product_variant_payload(product_with_single_variant.variants.all())
        )[0]
    )
    test_template_id = "2efac70d-64ed-4e57-9951-f87e14d7e60e"

    variables = {
        "input": {
            "ids": [to_global_id(User.__name__, user.id) for user in staff_users],
            "extraPayload": payload,
            "externalEventType": test_template_id,
        },
        "pluginId": "mirumee.notifications.sendgrid_email",
    }

    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_users],
    )

    assert response.status_code == 200
    assert notify_single_plugin_mock.call_count == 3


@patch("saleor.plugins.sendgrid.plugin.EVENT_MAP")
def test_notify_when_plugin_disabled(mocked_event_map, sendgrid_email_plugin):
    mocked_event_task = MagicMock()
    event_map = {
        UserNotifyEvent.ACCOUNT_PASSWORD_RESET: (
            mocked_event_task,
            "account_password_reset_template_id",
        )
    }
    mocked_event_map.__getitem__.side_effect = event_map.__getitem__
    mocked_event_map.get.side_effect = event_map.get

    plugin = sendgrid_email_plugin(active=False)

    plugin.notify(UserNotifyEvent.ACCOUNT_PASSWORD_RESET, {}, None)

    assert not mocked_event_task.delay.called


@patch("saleor.plugins.sendgrid.plugin.EVENT_MAP")
def test_notify_not_valid_event_type(mocked_event_map, sendgrid_email_plugin):
    mocked_event_task = MagicMock()
    event_map = {
        UserNotifyEvent.ACCOUNT_PASSWORD_RESET: (
            mocked_event_task,
            "account_password_reset_template_id",
        )
    }
    mocked_event_map.__getitem__.side_effect = event_map.__getitem__
    mocked_event_map.get.side_effect = event_map.get

    plugin = sendgrid_email_plugin(api_key="AB12", active=True)

    plugin.notify(AdminNotifyEvent.CSV_EXPORT_FAILED, {}, None)

    assert not mocked_event_task.delay.called


@patch("saleor.plugins.sendgrid.plugin.EVENT_MAP")
def test_notify_missing_handler(mocked_event_map, sendgrid_email_plugin):
    sample_payload = {"key_1": "value"}

    mocked_event_task = MagicMock()
    event_map = {
        UserNotifyEvent.ACCOUNT_CHANGE_EMAIL_REQUEST: (
            mocked_event_task,
            "account_password_reset_template_id",
        )
    }
    mocked_event_map.__contains__.side_effect = event_map.__contains__

    plugin = sendgrid_email_plugin(api_key="AB12", active=True)

    plugin.notify(UserNotifyEvent.ACCOUNT_PASSWORD_RESET, sample_payload, None)

    assert mocked_event_map.__contains__.called
    assert not mocked_event_task.delay.called


@patch("saleor.plugins.sendgrid.plugin.EVENT_MAP")
def test_notify_missing_template_id(mocked_event_map, sendgrid_email_plugin):
    sample_payload = {"key_1": "value"}

    mocked_event_task = MagicMock()
    event_map = {
        UserNotifyEvent.ACCOUNT_PASSWORD_RESET: (
            mocked_event_task,
            "account_password_reset_template_id",
        )
    }
    mocked_event_map.__getitem__.side_effect = event_map.__getitem__
    mocked_event_map.__contains__.return_value = True
    mocked_event_map.get.side_effect = event_map.get

    plugin = sendgrid_email_plugin(
        active=True, api_key="AB12", account_password_reset_template_id=None
    )

    plugin.notify(UserNotifyEvent.ACCOUNT_PASSWORD_RESET, sample_payload, None)

    assert mocked_event_map.get.called
    assert not mocked_event_task.delay.called


@patch("saleor.plugins.sendgrid.plugin.EVENT_MAP")
def test_notify(mocked_event_map, sendgrid_email_plugin):
    sample_payload = {"key_1": "value"}

    mocked_event_task = MagicMock()
    event_map = {
        UserNotifyEvent.ACCOUNT_PASSWORD_RESET: (
            mocked_event_task,
            "account_password_reset_template_id",
        )
    }
    mocked_event_map.__getitem__.side_effect = event_map.__getitem__
    mocked_event_map.__contains__.return_value = True
    mocked_event_map.get.side_effect = event_map.get

    plugin = sendgrid_email_plugin(
        active=True, api_key="AB12", account_password_reset_template_id="123"
    )

    plugin.notify(UserNotifyEvent.ACCOUNT_PASSWORD_RESET, sample_payload, None)

    mocked_event_task.delay.assert_called_once_with(
        sample_payload, asdict(plugin.config)
    )


def test_save_plugin_configuration_missing_api_key(
    sendgrid_email_plugin,
):
    plugin = sendgrid_email_plugin(active=False)
    configuration = PluginConfiguration.objects.get()

    data_to_save = {"active": True, "configuration": []}
    with pytest.raises(ValidationError):
        plugin.save_plugin_configuration(configuration, data_to_save)
