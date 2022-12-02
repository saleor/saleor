from dataclasses import asdict
from smtplib import SMTPNotSupportedError
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.core.exceptions import ValidationError
from django.core.mail.backends.smtp import EmailBackend

from ....core.notify_events import NotifyEventType
from ....graphql.tests.utils import get_graphql_content
from ...email_common import DEFAULT_EMAIL_VALUE, get_email_template
from ...manager import get_plugins_manager
from ...models import PluginConfiguration
from ..constants import (
    CSV_EXPORT_FAILED_TEMPLATE_FIELD,
    CSV_EXPORT_SUCCESS_TEMPLATE_FIELD,
    SET_STAFF_PASSWORD_TEMPLATE_FIELD,
    STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD,
)
from ..notify_events import (
    send_csv_export_failed,
    send_csv_export_success,
    send_set_staff_password_email,
    send_staff_order_confirmation,
    send_staff_reset_password,
)
from ..plugin import get_admin_event_map


def test_event_map():
    assert get_admin_event_map() == {
        NotifyEventType.STAFF_ORDER_CONFIRMATION: send_staff_order_confirmation,
        NotifyEventType.ACCOUNT_SET_STAFF_PASSWORD: send_set_staff_password_email,
        NotifyEventType.CSV_EXPORT_SUCCESS: send_csv_export_success,
        NotifyEventType.CSV_EXPORT_FAILED: send_csv_export_failed,
        NotifyEventType.ACCOUNT_STAFF_RESET_PASSWORD: send_staff_reset_password,
    }


@pytest.mark.parametrize(
    "event_type",
    [
        NotifyEventType.STAFF_ORDER_CONFIRMATION,
        NotifyEventType.ACCOUNT_SET_STAFF_PASSWORD,
        NotifyEventType.CSV_EXPORT_SUCCESS,
        NotifyEventType.CSV_EXPORT_FAILED,
        NotifyEventType.ACCOUNT_STAFF_RESET_PASSWORD,
    ],
)
@patch("saleor.plugins.admin_email.plugin.get_admin_event_map")
def test_notify(mocked_get_event_map, event_type, admin_email_plugin):
    payload = {
        "field1": 1,
        "field2": 2,
    }
    mocked_event = Mock()
    mocked_get_event_map.return_value = {event_type: mocked_event}

    plugin = admin_email_plugin()
    plugin.notify(event_type, payload, previous_value=None)

    mocked_event.assert_called_with(payload, asdict(plugin.config), plugin)


@patch("saleor.plugins.admin_email.plugin.get_admin_event_map")
def test_notify_event_not_related(mocked_get_event_map, admin_email_plugin):
    event_type = NotifyEventType.ACCOUNT_SET_CUSTOMER_PASSWORD
    payload = {
        "field1": 1,
        "field2": 2,
    }

    mocked_event = Mock()
    mocked_get_event_map.return_value = {event_type: mocked_event}

    plugin = admin_email_plugin()
    plugin.notify(event_type, payload, previous_value=None)

    assert not mocked_event.called


@patch("saleor.plugins.admin_email.plugin.get_admin_event_map")
def test_notify_event_missing_handler(mocked_get_event_map, admin_email_plugin):
    event_type = NotifyEventType.CSV_EXPORT_FAILED
    payload = {
        "field1": 1,
        "field2": 2,
    }

    mocked_event_map = MagicMock()
    mocked_get_event_map.return_value = mocked_event_map

    plugin = admin_email_plugin()
    plugin.notify(event_type, payload, previous_value=None)

    assert not mocked_event_map.__getitem__.called


@patch("saleor.plugins.admin_email.plugin.get_admin_event_map")
def test_notify_event_plugin_is_not_active(mocked_get_event_map, admin_email_plugin):
    event_type = NotifyEventType.CSV_EXPORT_FAILED
    payload = {
        "field1": 1,
        "field2": 2,
    }

    plugin = admin_email_plugin(active=False)
    plugin.notify(event_type, payload, previous_value=None)

    assert not mocked_get_event_map.called


def test_save_plugin_configuration_tls_and_ssl_are_mutually_exclusive(
    admin_email_plugin,
):
    plugin = admin_email_plugin()
    configuration = PluginConfiguration.objects.get()
    data_to_save = {
        "configuration": [
            {"name": "use_tls", "value": True},
            {"name": "use_ssl", "value": True},
        ]
    }
    with pytest.raises(ValidationError):
        plugin.save_plugin_configuration(configuration, data_to_save)


@patch.object(EmailBackend, "open")
def test_save_plugin_configuration(mocked_open, admin_email_plugin):
    plugin = admin_email_plugin()
    configuration = PluginConfiguration.objects.get()
    data_to_save = {
        "configuration": [
            {"name": "use_tls", "value": False},
            {"name": "use_ssl", "value": True},
        ]
    }

    plugin.save_plugin_configuration(configuration, data_to_save)

    mocked_open.assert_called_with()


@patch.object(EmailBackend, "open")
def test_save_plugin_configuration_incorrect_email_backend_configuration(
    mocked_open, admin_email_plugin
):
    plugin = admin_email_plugin()
    mocked_open.side_effect = SMTPNotSupportedError()
    configuration = PluginConfiguration.objects.get()
    data_to_save = {
        "configuration": [
            {"name": "use_tls", "value": False},
            {"name": "use_ssl", "value": True},
        ]
    }

    with pytest.raises(ValidationError):
        plugin.save_plugin_configuration(configuration, data_to_save)


@patch.object(EmailBackend, "open")
def test_save_plugin_configuration_incorrect_template(mocked_open, admin_email_plugin):
    incorrect_template_str = """
    {{#if order.order_details_url}}
      Thank you for your order. Below is the list of fulfilled products. To see your
      order details please visit:
      <a href="{{ order.order_details_url }}">{{ order.order_details_url }}</a>
    {{else}}
      Thank you for your order. Below is the list of fulfilled products.
    {{/if}
    """  # missing } at the end of the if condition

    plugin = admin_email_plugin()
    configuration = PluginConfiguration.objects.get()

    data_to_save = {
        "configuration": [
            {
                "name": STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD,
                "value": incorrect_template_str,
            },
            {
                "name": SET_STAFF_PASSWORD_TEMPLATE_FIELD,
                "value": incorrect_template_str,
            },
            {
                "name": CSV_EXPORT_SUCCESS_TEMPLATE_FIELD,
                "value": incorrect_template_str,
            },
            {"name": CSV_EXPORT_FAILED_TEMPLATE_FIELD, "value": incorrect_template_str},
        ]
    }

    with pytest.raises(ValidationError):
        plugin.save_plugin_configuration(configuration, data_to_save)

    mocked_open.assert_called_with()


def test_get_email_template(admin_email_plugin, admin_email_template):
    plugin = admin_email_plugin()
    default = "Default template"
    template = get_email_template(plugin, admin_email_template.name, default)
    assert template == admin_email_template.value

    admin_email_template.delete()
    template = get_email_template(plugin, admin_email_template.name, default)
    assert template == default


@patch.object(EmailBackend, "open")
def test_save_plugin_configuration_creates_email_template_instance(
    mocked_open, admin_email_plugin
):
    template_str = """Thank you for your order."""

    plugin = admin_email_plugin()
    configuration = PluginConfiguration.objects.get()

    data_to_save = {
        "configuration": [
            {
                "name": STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD,
                "value": template_str,
            }
        ]
    }

    plugin.save_plugin_configuration(configuration, data_to_save)
    configuration.refresh_from_db()

    email_template = configuration.email_templates.get()
    assert email_template
    assert email_template.name == STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD
    assert email_template.value == template_str


QUERY_GET_PLUGIN = """
  query Plugin($id: ID!) {
    plugin(id: $id) {
      id
      name
      globalConfiguration {
        configuration {
          name
          value
        }
      }
    }
  }
"""


def test_configuration_resolver_returns_email_template_value(
    staff_api_client,
    admin_email_plugin,
    admin_email_template,
    permission_manage_plugins,
):
    plugin = admin_email_plugin()
    response = staff_api_client.post_graphql(
        QUERY_GET_PLUGIN,
        {"id": plugin.PLUGIN_ID},
        permissions=(permission_manage_plugins,),
    )
    content = get_graphql_content(response)
    data = content["data"]["plugin"]

    email_config_item = None
    for config_item in data["globalConfiguration"]["configuration"]:
        if config_item["name"] == admin_email_template.name:
            email_config_item = config_item

    assert email_config_item
    assert email_config_item["value"] == admin_email_template.value


def test_plugin_manager_doesnt_load_email_templates_from_db(
    admin_email_plugin, admin_email_template, settings
):
    settings.PLUGINS = ["saleor.plugins.admin_email.plugin.AdminEmailPlugin"]
    manager = get_plugins_manager()
    plugin = manager.all_plugins[0]

    email_config_item = None
    for config_item in plugin.configuration:
        if config_item["name"] == admin_email_template.name:
            email_config_item = config_item

    # Assert that accessing plugin configuration directly from manager doesn't load
    # email template from DB but returns default email value.
    assert email_config_item
    assert email_config_item["value"] == DEFAULT_EMAIL_VALUE
