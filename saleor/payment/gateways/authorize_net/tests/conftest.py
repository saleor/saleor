from unittest import mock

import pytest

from .....plugins.manager import get_plugins_manager
from ....interface import GatewayConfig
from ..plugin import AuthorizeNetGatewayPlugin


@pytest.fixture
def authorize_net_gateway_config():
    return GatewayConfig(
        gateway_name="authorize_net",
        auto_capture=True,
        supported_currencies="USD",
        connection_params={
            "api_login_id": "public",
            "transaction_key": "secret",
            "client_key": "public",
            "use_sandbox": True,
        },
    )


@pytest.fixture()
def authorize_net_payment(payment_dummy):
    payment_dummy.gateway = "mirumee.payments.authorize_net"
    return payment_dummy


@pytest.fixture
@mock.patch(
    "saleor.payment.gateways.authorize_net.plugin.AuthorizeNetGatewayPlugin"
    ".validate_plugin_configuration"
)
def authorize_net_plugin(_, settings, channel_USD, authorize_net_gateway_config):
    settings.PLUGINS = [
        "saleor.payment.gateways.authorize_net.plugin.AuthorizeNetGatewayPlugin"
    ]
    manager = get_plugins_manager()

    connection_params = authorize_net_gateway_config.connection_params

    manager.save_plugin_configuration(
        AuthorizeNetGatewayPlugin.PLUGIN_ID,
        channel_USD.slug,
        {
            "active": True,
            "configuration": [
                {"name": "api_login_id", "value": connection_params["api_login_id"]},
                {
                    "name": "transaction_key",
                    "value": connection_params["transaction_key"],
                },
                {"name": "client_key", "value": connection_params["client_key"]},
                {"name": "use_sandbox", "value": connection_params["use_sandbox"]},
                {
                    "name": "store_customers_card",
                    "value": authorize_net_gateway_config.store_customer,
                },
                {
                    "name": "automatic_payment_capture",
                    "value": authorize_net_gateway_config.auto_capture,
                },
                {
                    "name": "supported_currencies",
                    "value": authorize_net_gateway_config.supported_currencies,
                },
            ],
        },
    )

    manager = get_plugins_manager()
    return manager.plugins_per_channel[channel_USD.slug][0]
