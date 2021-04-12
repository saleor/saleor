from dataclasses import asdict
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ValidationError

from ....core.notify_events import AdminNotifyEvent, UserNotifyEvent
from ...models import PluginConfiguration
from ..plugin import EVENT_MAP


def test_get_event_map():
    for event in UserNotifyEvent.CHOICES:
        assert event in EVENT_MAP


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
