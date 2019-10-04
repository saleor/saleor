import pytest

from saleor.dashboard.payment.forms import GatewayConfigurationForm
from saleor.extensions.models import PluginConfiguration
from saleor.payment.gateways.braintree.plugin import BraintreeGatewayPlugin


@pytest.fixture
def plugin_configuration(db):
    plugin_configuration = PluginConfiguration.objects.create(
        **BraintreeGatewayPlugin._get_default_configuration()
    )

    config = [
        {"name": "Public API key", "value": "123456"},
        {"name": "Secret API key", "value": "654321"},
        {"name": "Merchant ID", "value": "0987654321"},
        {"name": "Use sandbox", "value": False},
        {"name": "Store customers card", "value": False},
        {"name": "Automatic payment capture", "value": False},
        {"name": "Require 3D secure", "value": True},
    ]

    BraintreeGatewayPlugin._update_config_items(
        config, plugin_configuration.configuration
    )
    plugin_configuration.active = True
    plugin_configuration.save()
    return plugin_configuration


@pytest.fixture(autouse=True)
def enable_plugin(settings):
    settings.PLUGINS = [
        "saleor.payment.gateways.braintree.plugin.BraintreeGatewayPlugin"
    ]


def test_configuration_form_get_current_configuration(plugin_configuration):
    form = GatewayConfigurationForm(BraintreeGatewayPlugin)
    assert form._get_current_configuration() == plugin_configuration
