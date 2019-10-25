import pytest

from saleor.extensions import ConfigurationTypeField
from saleor.extensions.base_plugin import BasePlugin
from saleor.extensions.models import PluginConfiguration


class PluginSample(BasePlugin):
    PLUGIN_NAME = "PluginSample"
    CONFIG_STRUCTURE = {
        "Username": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Username of Sample account",
            "label": "Username",
        },
        "Use sandbox": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Select if you want to test this integration",
            "label": "Use sandbox",
        },
    }

    @classmethod
    def _get_default_configuration(cls):
        defaults = {
            "name": cls.PLUGIN_NAME,
            "description": "",
            "active": True,
            "configuration": [
                {"name": "Username", "value": "admin@example.com"},
                {"name": "Use sandbox", "value": True},
            ],
        }
        return defaults


@pytest.fixture(autouse=True)
def settings_plugins(settings):
    settings.PLUGINS = [
        "saleor.extensions.plugins.avatax.plugin.AvataxPlugin",
        "saleor.extensions.plugins.vatlayer.plugin.VatlayerPlugin",
        "saleor.extensions.plugins.webhook.plugin.WebhookPlugin",
        "saleor.payment.gateways.dummy.plugin.DummyGatewayPlugin",
        "saleor.payment.gateways.stripe.plugin.StripeGatewayPlugin",
        "saleor.payment.gateways.braintree.plugin.BraintreeGatewayPlugin",
        "saleor.payment.gateways.razorpay.plugin.RazorpayGatewayPlugin",
    ]


def get_config_value(field_name, configuration):
    for elem in configuration:
        if elem["name"] == field_name:
            return elem["value"]


def test_update_config_items_keeps_bool_value():
    data_to_update = [
        {"name": "Username", "value": "new_admin@example.com"},
        {"name": "Use sandbox", "value": False},
    ]
    plugin_sample = PluginSample()
    plugin_sample._initialize_plugin_configuration()
    qs = PluginConfiguration.objects.all()
    configuration = PluginSample.get_plugin_configuration(qs)
    plugin_sample._update_config_items(data_to_update, configuration.configuration)
    configuration.save()
    configuration.refresh_from_db()
    assert get_config_value("Use sandbox", configuration.configuration) is False


def test_update_config_items_convert_to_bool_value():
    data_to_update = [
        {"name": "Username", "value": "new_admin@example.com"},
        {"name": "Use sandbox", "value": "false"},
    ]
    plugin_sample = PluginSample()
    plugin_sample._initialize_plugin_configuration()
    qs = PluginConfiguration.objects.all()
    configuration = PluginSample.get_plugin_configuration(qs)
    plugin_sample._update_config_items(data_to_update, configuration.configuration)
    configuration.save()
    configuration.refresh_from_db()
    assert get_config_value("Use sandbox", configuration.configuration) is False
