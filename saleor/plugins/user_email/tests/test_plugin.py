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
    ORDER_CONFIRMATION_TEMPLATE_FIELD,
    ORDER_CONFIRMED_TEMPLATE_FIELD,
)
from ..notify_events import (
    send_account_change_email_confirm,
    send_account_change_email_request,
    send_account_confirmation,
    send_account_delete,
    send_account_password_reset_event,
    send_account_set_customer_password,
    send_fulfillment_confirmation,
    send_fulfillment_update,
    send_gift_card,
    send_invoice,
    send_order_canceled,
    send_order_confirmation,
    send_order_confirmed,
    send_order_refund,
    send_payment_confirmation,
)
from ..plugin import get_user_event_map


def test_event_map():
    assert get_user_event_map() == {
        NotifyEventType.ACCOUNT_CONFIRMATION: send_account_confirmation,
        NotifyEventType.ACCOUNT_SET_CUSTOMER_PASSWORD: (
            send_account_set_customer_password
        ),
        NotifyEventType.ACCOUNT_DELETE: send_account_delete,
        NotifyEventType.ACCOUNT_CHANGE_EMAIL_CONFIRM: send_account_change_email_confirm,
        NotifyEventType.ACCOUNT_CHANGE_EMAIL_REQUEST: send_account_change_email_request,
        NotifyEventType.ACCOUNT_PASSWORD_RESET: send_account_password_reset_event,
        NotifyEventType.INVOICE_READY: send_invoice,
        NotifyEventType.ORDER_CONFIRMATION: send_order_confirmation,
        NotifyEventType.ORDER_FULFILLMENT_CONFIRMATION: send_fulfillment_confirmation,
        NotifyEventType.ORDER_FULFILLMENT_UPDATE: send_fulfillment_update,
        NotifyEventType.ORDER_PAYMENT_CONFIRMATION: send_payment_confirmation,
        NotifyEventType.ORDER_CANCELED: send_order_canceled,
        NotifyEventType.ORDER_REFUND_CONFIRMATION: send_order_refund,
        NotifyEventType.ORDER_CONFIRMED: send_order_confirmed,
        NotifyEventType.SEND_GIFT_CARD: send_gift_card,
    }


@pytest.mark.parametrize(
    "event_type",
    [
        NotifyEventType.ACCOUNT_CONFIRMATION,
        NotifyEventType.ACCOUNT_SET_CUSTOMER_PASSWORD,
        NotifyEventType.ACCOUNT_DELETE,
        NotifyEventType.ACCOUNT_CHANGE_EMAIL_CONFIRM,
        NotifyEventType.ACCOUNT_CHANGE_EMAIL_REQUEST,
        NotifyEventType.ACCOUNT_PASSWORD_RESET,
        NotifyEventType.INVOICE_READY,
        NotifyEventType.ORDER_CONFIRMATION,
        NotifyEventType.ORDER_FULFILLMENT_CONFIRMATION,
        NotifyEventType.ORDER_FULFILLMENT_UPDATE,
        NotifyEventType.ORDER_PAYMENT_CONFIRMATION,
        NotifyEventType.ORDER_CANCELED,
        NotifyEventType.ORDER_REFUND_CONFIRMATION,
        NotifyEventType.SEND_GIFT_CARD,
    ],
)
@patch("saleor.plugins.user_email.plugin.get_user_event_map")
def test_notify(mocked_get_event_map, event_type, user_email_plugin):
    payload = {
        "field1": 1,
        "field2": 2,
    }
    mocked_event = Mock()
    mocked_get_event_map.return_value = {event_type: mocked_event}

    plugin = user_email_plugin()
    plugin.notify(event_type, payload, previous_value=None)

    mocked_event.assert_called_with(payload, asdict(plugin.config), plugin)


@patch("saleor.plugins.user_email.plugin.get_user_event_map")
def test_notify_event_not_related(mocked_get_event_map, user_email_plugin):
    event_type = NotifyEventType.STAFF_ORDER_CONFIRMATION
    payload = {
        "field1": 1,
        "field2": 2,
    }
    mocked_event = Mock()
    mocked_get_event_map.return_value = {event_type: mocked_event}

    plugin = user_email_plugin()
    plugin.notify(event_type, payload, previous_value=None)

    assert not mocked_event.called


@patch("saleor.plugins.user_email.plugin.get_user_event_map")
def test_notify_event_missing_handler(mocked_get_event_map, user_email_plugin):
    event_type = NotifyEventType.ORDER_PAYMENT_CONFIRMATION
    payload = {
        "field1": 1,
        "field2": 2,
    }
    mocked_event_map = MagicMock()
    mocked_get_event_map.return_value = mocked_event_map

    plugin = user_email_plugin()
    plugin.notify(event_type, payload, previous_value=None)

    assert not mocked_event_map.__getitem__.called


@patch("saleor.plugins.user_email.plugin.get_user_event_map")
def test_notify_event_plugin_is_not_active(mocked_get_event_map, user_email_plugin):
    event_type = NotifyEventType.ORDER_PAYMENT_CONFIRMATION
    payload = {
        "field1": 1,
        "field2": 2,
    }

    plugin = user_email_plugin(active=False)
    plugin.notify(event_type, payload, previous_value=None)

    assert not mocked_get_event_map.called


def test_save_plugin_configuration_tls_and_ssl_are_mutually_exclusive(
    user_email_plugin,
):
    plugin = user_email_plugin()
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
def test_save_plugin_configuration(mocked_open, user_email_plugin):
    plugin = user_email_plugin()
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
    mocked_open, user_email_plugin
):
    plugin = user_email_plugin()
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
    mocked_open.assert_called_with()


@patch.object(EmailBackend, "open")
def test_save_plugin_configuration_incorrect_template(mocked_open, user_email_plugin):
    incorrect_template_str = """
    {{#if order.order_details_url}}
      Thank you for your order. Below is the list of fulfilled products. To see your
      order details please visit:
      <a href="{{ order.order_details_url }}">{{ order.order_details_url }}</a>
    {{else}}
      Thank you for your order. Below is the list of fulfilled products.
    {{/if}
    """  # missing } at the end of the if condition

    plugin = user_email_plugin()
    configuration = PluginConfiguration.objects.get()
    data_to_save = {
        "configuration": [
            {
                "name": ORDER_CONFIRMATION_TEMPLATE_FIELD,
                "value": incorrect_template_str,
            },
            {"name": ORDER_CONFIRMED_TEMPLATE_FIELD, "value": incorrect_template_str},
        ]
    }

    with pytest.raises(ValidationError):
        plugin.save_plugin_configuration(configuration, data_to_save)
    mocked_open.assert_called_with()


def test_get_email_template(user_email_plugin, user_email_template):
    plugin = user_email_plugin()
    default = "Default template"
    template = get_email_template(plugin, user_email_template.name, default)
    assert template == user_email_template.value

    user_email_template.delete()
    template = get_email_template(plugin, user_email_template.name, default)
    assert template == default


@patch.object(EmailBackend, "open")
def test_save_plugin_configuration_creates_email_template_instance(
    mocked_open, user_email_plugin
):
    template_str = """Thank you for your order."""

    plugin = user_email_plugin()
    configuration = PluginConfiguration.objects.get()

    data_to_save = {
        "configuration": [
            {
                "name": ORDER_CONFIRMATION_TEMPLATE_FIELD,
                "value": template_str,
            }
        ]
    }

    plugin.save_plugin_configuration(configuration, data_to_save)
    configuration.refresh_from_db()

    email_template = configuration.email_templates.get()
    assert email_template
    assert email_template.name == ORDER_CONFIRMATION_TEMPLATE_FIELD
    assert email_template.value == template_str


QUERY_GET_PLUGIN = """
  query Plugin($id: ID!) {
    plugin(id: $id) {
      id
      name
      channelConfigurations {
        channel {
          slug
        }
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
    user_email_plugin,
    user_email_template,
    permission_manage_plugins,
):
    plugin = user_email_plugin()
    response = staff_api_client.post_graphql(
        QUERY_GET_PLUGIN,
        {"id": plugin.PLUGIN_ID},
        permissions=(permission_manage_plugins,),
    )
    content = get_graphql_content(response)
    data = content["data"]["plugin"]

    email_config_item = None
    for config_item in data["channelConfigurations"][0]["configuration"]:
        if config_item["name"] == user_email_template.name:
            email_config_item = config_item

    assert email_config_item
    assert email_config_item["value"] == user_email_template.value


def test_plugin_manager_doesnt_load_email_templates_from_db(
    user_email_plugin, user_email_template, settings
):
    settings.PLUGINS = ["saleor.plugins.user_email.plugin.UserEmailPlugin"]
    manager = get_plugins_manager()
    plugin = manager.all_plugins[0]

    email_config_item = None
    for config_item in plugin.configuration:
        if config_item["name"] == user_email_template.name:
            email_config_item = config_item

    # Assert that accessing plugin configuration directly from manager doesn't load
    # email template from DB but returns default email value.
    assert email_config_item
    assert email_config_item["value"] == DEFAULT_EMAIL_VALUE
