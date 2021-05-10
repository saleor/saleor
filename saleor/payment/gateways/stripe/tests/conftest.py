from unittest import mock

import pytest

from .....plugins.manager import get_plugins_manager
from ..plugin import StripeGatewayPlugin


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": [("Authorization", "test_key")],
    }


@pytest.fixture
def stripe_plugin(settings, monkeypatch):
    def fun(
        public_api_key=None,
        secret_api_key=None,
        webhook_endpoint_id=None,
        webhook_secret_key=None,
    ):
        public_api_key = public_api_key or "test_key"
        secret_api_key = secret_api_key or "secret_key"
        webhook_endpoint_id = webhook_endpoint_id or "12345"
        webhook_secret_key = webhook_secret_key or "ABCD"

        settings.PLUGINS = ["saleor.payment.gateways.stripe.plugin.StripeGatewayPlugin"]
        manager = get_plugins_manager()

        validate_method_path = (
            "saleor.payment.gateways.stripe.plugin.StripeGatewayPlugin."
            "validate_plugin_configuration"
        )
        pre_save_method_path = (
            "saleor.payment.gateways.stripe.plugin.StripeGatewayPlugin."
            "pre_save_plugin_configuration"
        )

        with mock.patch(validate_method_path), mock.patch(pre_save_method_path):
            manager.save_plugin_configuration(
                StripeGatewayPlugin.PLUGIN_ID,
                {
                    "active": True,
                    "configuration": [
                        {"name": "public_api_key", "value": public_api_key},
                        {"name": "secret_api_key", "value": secret_api_key},
                        {"name": "store_customers_cards", "value": False},
                        {"name": "automatic_payment_capture", "value": True},
                        {"name": "supported_currencies", "value": "USD"},
                        {"name": "webhook_endpoint_id", "value": webhook_endpoint_id},
                        {"name": "webhook_secret_key", "value": webhook_secret_key},
                    ],
                },
            )

        manager = get_plugins_manager()
        return manager.plugins[0]

    return fun
