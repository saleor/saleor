import json
from dataclasses import asdict
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ValidationError

from ....account.notifications import get_user_custom_payload
from ....core.notify_events import AdminNotifyEvent, UserNotifyEvent
from ....webhook.payloads import generate_product_variant_payload
from ...models import PluginConfiguration
from ..plugin import EVENT_MAP


def test_get_event_map():
    for event in UserNotifyEvent.CHOICES:
        assert event in EVENT_MAP


@patch("saleor.plugins.sendgrid.tasks.send_email_with_dynamic_template_id.delay")
def test_notify_via_external_notification_trigger_with_extra_payload(
    mocked_event_map,
    staff_users,
    sendgrid_email_plugin,
):

    extra_payload = {"TEST": "VALUE", "TEST_LIST": ["GUEST1", "GUEST2"]}
    plugin = sendgrid_email_plugin(
        active=True, api_key="AB12", account_password_reset_template_id="123"
    )

    expected_payload = [get_user_custom_payload(user) for user in staff_users]
    for payload in expected_payload:
        payload["extra_payload"] = extra_payload
    test_template_id = "2efac70d-64ed-4e57-9951-f87e14d7e60e"
    plugin.notify(test_template_id, expected_payload, None)

    mocked_event_map.assert_called_once_with(
        expected_payload, test_template_id, asdict(plugin.config)
    )


@patch("sendgrid.base_interface.BaseInterface.send")
def test_send_notification_to_customers_with_product_variant_payload(
    base_interface_mock,
    staff_users,
    sendgrid_email_plugin,
    product_with_single_variant,
):

    plugin = sendgrid_email_plugin(active=True, api_key="AB12")
    extra_payload = json.dumps(
        json.loads(
            generate_product_variant_payload(product_with_single_variant.variants.all())
        )[0]
    )

    expected_payload = [get_user_custom_payload(user) for user in staff_users]
    for payload in expected_payload:
        payload["extra_payload"] = extra_payload

    test_template_id = "2efac70d-64ed-4e57-9951-f87e14d7e60e"

    plugin.notify(test_template_id, expected_payload[0], None)

    base_interface_mock.assert_called_once()


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
