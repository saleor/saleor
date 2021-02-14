from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ValidationError

from ....core.notify_events import AdminNotifyEvent, UserNotifyEvent
from ...models import PluginConfiguration
from .. import tasks
from ..plugin import get_event_to_task_map


def test_get_event_to_task_map():
    assert get_event_to_task_map() == {
        UserNotifyEvent.ACCOUNT_CONFIRMATION: (
            tasks.send_account_confirmation_email_task
        ),
        UserNotifyEvent.ACCOUNT_SET_CUSTOMER_PASSWORD: (
            tasks.send_set_user_password_email_task
        ),
        UserNotifyEvent.ACCOUNT_DELETE: (
            tasks.send_account_delete_confirmation_email_task
        ),
        UserNotifyEvent.ACCOUNT_CHANGE_EMAIL_CONFIRM: (
            tasks.send_user_change_email_notification_task
        ),
        UserNotifyEvent.ACCOUNT_CHANGE_EMAIL_REQUEST: (
            tasks.send_request_email_change_email_task
        ),
        UserNotifyEvent.ACCOUNT_PASSWORD_RESET: tasks.send_password_reset_email_task,
        UserNotifyEvent.INVOICE_READY: tasks.send_invoice_email_task,
        UserNotifyEvent.ORDER_CONFIRMATION: tasks.send_order_confirmation_email_task,
        UserNotifyEvent.ORDER_CONFIRMED: tasks.send_order_confirmed_email_task,
        UserNotifyEvent.ORDER_FULFILLMENT_CONFIRMATION: (
            tasks.send_fulfillment_confirmation_email_task
        ),
        UserNotifyEvent.ORDER_FULFILLMENT_UPDATE: (
            tasks.send_fulfillment_update_email_task
        ),
        UserNotifyEvent.ORDER_PAYMENT_CONFIRMATION: (
            tasks.send_payment_confirmation_email_task
        ),
        UserNotifyEvent.ORDER_CANCELED: tasks.send_order_canceled_email_task,
        UserNotifyEvent.ORDER_REFUND_CONFIRMATION: tasks.send_order_refund_email_task,
    }


@patch("saleor.plugins.sendgrid.plugin.get_event_to_task_map")
def test_notify_when_plugin_disabled(
    mocked_get_event_to_task_map, sendgrid_email_plugin
):
    plugin = sendgrid_email_plugin(active=False)

    plugin.notify(UserNotifyEvent.ACCOUNT_PASSWORD_RESET, {}, None)

    assert not mocked_get_event_to_task_map.called


@patch("saleor.plugins.sendgrid.plugin.get_event_to_task_map")
def test_notify_not_valid_event_type(
    mocked_get_event_to_task_map, sendgrid_email_plugin
):
    plugin = sendgrid_email_plugin(api_key="AB12", active=True)

    plugin.notify(AdminNotifyEvent.CSV_EXPORT_FAILED, {}, None)

    assert not mocked_get_event_to_task_map.called


@patch("saleor.plugins.sendgrid.plugin.get_event_to_task_map")
def test_notify_missing_handler(mocked_get_event_to_task_map, sendgrid_email_plugin):
    sample_payload = {"key_1": "value"}

    event_map = MagicMock()
    mocked_get_event_to_task_map.return_value = event_map

    plugin = sendgrid_email_plugin(api_key="AB12", active=True)

    plugin.notify(UserNotifyEvent.ACCOUNT_PASSWORD_RESET, sample_payload, None)

    assert mocked_get_event_to_task_map.called
    assert not event_map.__getitem__.called


@patch("saleor.plugins.sendgrid.plugin.get_event_to_task_map")
def test_notify_missing_template_id(
    mocked_get_event_to_task_map, sendgrid_email_plugin
):
    sample_payload = {"key_1": "value"}

    event_map = MagicMock()
    event_map.__contains__.return_value = True
    mocked_get_event_to_task_map.return_value = event_map

    plugin = sendgrid_email_plugin(
        active=True, api_key="AB12", account_password_reset_template_id=None
    )

    plugin.notify(UserNotifyEvent.ACCOUNT_PASSWORD_RESET, sample_payload, None)

    assert mocked_get_event_to_task_map.called
    assert not event_map.__getitem__.called


@patch("saleor.plugins.sendgrid.plugin.get_event_to_task_map")
def test_notify(mocked_get_event_to_task_map, sendgrid_email_plugin):
    sample_payload = {"key_1": "value"}

    event_map = MagicMock()
    event_map.__contains__.return_value = True
    mocked_get_event_to_task_map.return_value = event_map

    plugin = sendgrid_email_plugin(
        active=True, api_key="AB12", account_password_reset_template_id="123"
    )

    plugin.notify(UserNotifyEvent.ACCOUNT_PASSWORD_RESET, sample_payload, None)

    event_map.__getitem__.assert_called_once_with("account_password_reset")


def test_save_plugin_configuration_missing_api_key(
    sendgrid_email_plugin,
):
    plugin = sendgrid_email_plugin(active=False)
    configuration = PluginConfiguration.objects.get()

    data_to_save = {"active": True, "configuration": []}
    with pytest.raises(ValidationError):
        plugin.save_plugin_configuration(configuration, data_to_save)
