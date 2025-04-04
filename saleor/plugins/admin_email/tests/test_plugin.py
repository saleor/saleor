from dataclasses import asdict
from smtplib import SMTPNotSupportedError
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.core.exceptions import ValidationError
from django.core.mail.backends.smtp import EmailBackend

from ....core.notify import NotifyEventType
from ....graphql.tests.utils import get_graphql_content
from ...email_common import (
    DEFAULT_EMAIL_CONFIG_STRUCTURE,
    DEFAULT_EMAIL_VALUE,
    EmailConfig,
    get_email_template,
)
from ...manager import get_plugins_manager
from ...models import EmailTemplate, PluginConfiguration
from ..constants import (
    CSV_EXPORT_FAILED_TEMPLATE_FIELD,
    CSV_EXPORT_SUCCESS_TEMPLATE_FIELD,
    SET_STAFF_PASSWORD_TEMPLATE_FIELD,
    STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD,
    STAFF_PASSWORD_RESET_TEMPLATE_FIELD,
)
from ..notify_events import (
    send_csv_export_failed,
    send_csv_export_success,
    send_set_staff_password_email,
    send_staff_order_confirmation,
    send_staff_reset_password,
)
from ..plugin import AdminEmailPlugin, get_admin_event_map


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


def test_get_email_template(admin_email_plugin):
    assert EmailTemplate.objects.exists() is False

    staff_password_reset_template = "Custom staff reset password email template"
    plugin = admin_email_plugin(
        staff_password_reset_template=staff_password_reset_template
    )

    assert EmailTemplate.objects.exists() is True

    default = "Default template"
    template = get_email_template(plugin, STAFF_PASSWORD_RESET_TEMPLATE_FIELD, default)
    assert template == staff_password_reset_template

    EmailTemplate.objects.all().delete()

    template = get_email_template(plugin, STAFF_PASSWORD_RESET_TEMPLATE_FIELD, default)
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
    permission_manage_plugins,
):
    staff_password_reset_template = "Custom staff reset password email template"
    plugin = admin_email_plugin(
        staff_password_reset_template=staff_password_reset_template
    )
    response = staff_api_client.post_graphql(
        QUERY_GET_PLUGIN,
        {"id": plugin.PLUGIN_ID},
        permissions=(permission_manage_plugins,),
    )
    content = get_graphql_content(response)
    data = content["data"]["plugin"]

    email_config_item = None
    for config_item in data["globalConfiguration"]["configuration"]:
        if config_item["name"] == STAFF_PASSWORD_RESET_TEMPLATE_FIELD:
            email_config_item = config_item

    assert email_config_item
    assert email_config_item["value"] == staff_password_reset_template


def test_plugin_manager_doesnt_load_email_templates_from_db(
    admin_email_plugin, admin_email_template, settings
):
    settings.PLUGINS = ["saleor.plugins.admin_email.plugin.AdminEmailPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    manager.get_all_plugins()
    plugin = manager.all_plugins[0]
    assert EmailTemplate.objects.exists() is True

    email_config_item = None
    for config_item in plugin.configuration:
        if config_item["name"] == admin_email_template.name:
            email_config_item = config_item

    # Assert that accessing plugin configuration directly from manager doesn't load
    # email template from DB but returns default email value.
    assert email_config_item
    assert email_config_item["value"] == DEFAULT_EMAIL_VALUE


def test_plugin_dont_change_default_help_text_config_value():
    assert (
        AdminEmailPlugin.CONFIG_STRUCTURE["host"]["help_text"]
        != DEFAULT_EMAIL_CONFIG_STRUCTURE["host"]["help_text"]
    )
    assert (
        AdminEmailPlugin.CONFIG_STRUCTURE["port"]["help_text"]
        != DEFAULT_EMAIL_CONFIG_STRUCTURE["port"]["help_text"]
    )
    assert (
        AdminEmailPlugin.CONFIG_STRUCTURE["username"]["help_text"]
        != DEFAULT_EMAIL_CONFIG_STRUCTURE["username"]["help_text"]
    )
    assert (
        AdminEmailPlugin.CONFIG_STRUCTURE["password"]["help_text"]
        != DEFAULT_EMAIL_CONFIG_STRUCTURE["password"]["help_text"]
    )
    assert (
        AdminEmailPlugin.CONFIG_STRUCTURE["use_tls"]["help_text"]
        != DEFAULT_EMAIL_CONFIG_STRUCTURE["use_tls"]["help_text"]
    )
    assert (
        AdminEmailPlugin.CONFIG_STRUCTURE["use_ssl"]["help_text"]
        != DEFAULT_EMAIL_CONFIG_STRUCTURE["use_ssl"]["help_text"]
    )


def test_default_plugin_configuration(
    default_admin_email_plugin,
):
    default_email_from = "default@email.from"
    plugin = default_admin_email_plugin(
        default_email_from,
        email_url="smtp://some-user:secret-password@smtp.sendgrid.net:587/?tls=True",
    )
    assert plugin.active
    assert plugin.config.host == "smtp.sendgrid.net"
    assert plugin.config.port == "587"
    assert plugin.config.username == "some-user"
    assert plugin.config.password == "secret-password"
    assert plugin.config.sender_name == ""
    assert plugin.config.sender_address == default_email_from
    assert plugin.config.use_tls
    assert not plugin.config.use_ssl


@patch("saleor.plugins.email_common.validate_email_config")
def test_override_default_config(
    mocked_validate_email_config, default_admin_email_plugin
):
    """Assert that user-provided email config is not mixed with defaults."""
    plugin = default_admin_email_plugin(
        default_email_from="default@email.from",
        email_url="smtp://some-user:secret-password@smtp.sendgrid.net:587/?tls=True",
    )
    plugin_configuration = PluginConfiguration.objects.create(
        identifier=plugin.PLUGIN_ID,
        active=plugin.DEFAULT_ACTIVE,
        channel=None,
        configuration=plugin.configuration,
    )
    data_to_save = {
        "configuration": [
            {"name": "host", "value": "localhost"},
            {"name": "port", "value": "1025"},
            {"name": "sender_address", "value": "noreply@exmaple.com"},
        ]
    }
    expected_config = EmailConfig(
        host="localhost",
        port="1025",
        sender_name="",
        sender_address="noreply@exmaple.com",
        username="",  # empty as there's no username in data_to_save
        password="",  # empty as there's no password in data_to_save
        use_tls=False,
        use_ssl=False,
    )

    plugin.save_plugin_configuration(plugin_configuration, data_to_save)
    mocked_validate_email_config.assert_called_once_with(expected_config)

    # Assert that Django's EmailBackend does not override empty username and password
    email_backed = EmailBackend(
        host=expected_config.host,
        port=expected_config.port,
        username=expected_config.username,
        password=expected_config.password,
        use_ssl=expected_config.use_ssl,
        use_tls=expected_config.use_tls,
    )
    assert not email_backed.username
    assert not email_backed.password


@patch("saleor.plugins.email_common.validate_email_config")
def test_set_and_unset_custom_email_template(
    mocked_validate_email_config, admin_email_plugin
):
    # Set custom email template
    plugin = admin_email_plugin()
    configuration = PluginConfiguration.objects.get()
    data_to_save = {
        "configuration": [
            {
                "name": STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD,
                "value": "custom template",
            },
        ]
    }
    assert EmailTemplate.objects.exists() is False

    plugin.save_plugin_configuration(configuration, data_to_save)

    email_template = EmailTemplate.objects.get()
    assert email_template.name == STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD
    assert email_template.value == "custom template"

    # Unset custom email template
    data_to_save = {
        "configuration": [
            {
                "name": STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD,
                "value": DEFAULT_EMAIL_VALUE,
            },
        ]
    }

    plugin.save_plugin_configuration(configuration, data_to_save)

    assert EmailTemplate.objects.exists() is False
