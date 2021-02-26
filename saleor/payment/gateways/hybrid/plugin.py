from typing import TYPE_CHECKING, List
from django.conf import settings

from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField
from ..utils import get_supported_currencies

from ..dummy.plugin import DummyGatewayPlugin
from ..my_monchique_payment.plugin import MyMonchiqueGatewayPlugin
from ....payment.interface import (
    GatewayConfig, 
    PaymentData,
    GatewayResponse
)

if TYPE_CHECKING:
    # flake8: noqa
    from ....payment.interface import TokenConfig


def require_active_plugin(fn):
    def wrapped(self, *args, **kwargs):
        previous = kwargs.get("previous_value", None)
        if not self.active:
            return previous
        return fn(self, *args, **kwargs)

    return wrapped

GATEWAY_NAME = "Hybrid"

class HybridGatewayPlugin(BasePlugin):
    PLUGIN_ID = "quleap.payments.hybrid"
    PLUGIN_NAME = GATEWAY_NAME
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = "Saleor plugin to process payments with Monchique coins (mcoins) and Ayden Gateway"

    DEFAULT_CONFIGURATION = [
        {"name": "Public API key", "value": None},
        {"name": "Secret API key", "value": None},
        {"name": "Store customers card", "value": False},
        {"name": "Automatic payment capture", "value": True},
        {"name": "Supported currencies", "value": settings.DEFAULT_CURRENCY},
        {"name": "Require 3D secure", "value": False},
    ]

    CONFIG_STRUCTURE = {
        "Public API key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide  public API key.",
            "label": "Public API key",
        },
        "Secret API key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide Stripe secret API key.",
            "label": "Secret API key",
        },
        "Store customers card": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should store cards on payments "
            "in Stripe customer.",
            "label": "Store customers card",
        },
        "Automatic payment capture": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should automaticaly capture payments.",
            "label": "Automatic payment capture",
        },
        "Supported currencies": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Determines currencies supported by gateway."
            " Please enter currency codes separated by a comma.",
            "label": "Supported currencies",
        },
        "Require 3D secure": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if gateway should enforce 3D secure verification during payment"
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            auto_capture=configuration["Automatic payment capture"],
            supported_currencies=configuration["Supported currencies"],
            store_customer=configuration["Store customers card"],
            require_3d_secure=configuration["Require 3D secure"],
            connection_params={
                "public_key": configuration["Public API key"],
                "private_key": configuration["Secret API key"],
            },
        )

    def _get_gateway_config(self) -> GatewayConfig:
        return self.config

    @require_active_plugin
    def authorize_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        pass

    @require_active_plugin
    def capture_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        pass

    @require_active_plugin
    def refund_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        refund_monchique_result = MyMonchiqueGatewayPlugin.refund_payment(self, payment_information, previous_value)

        if refund_monchique_result.is_success:
            return DummyGatewayPlugin.refund_payment(self, payment_information, previous_value)
        
        return refund_monchique_result

    @require_active_plugin
    def void_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        pass

    @require_active_plugin
    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        process_monchique_result = MyMonchiqueGatewayPlugin.process_payment(self, payment_information, previous_value)

        if process_monchique_result.is_success:
            return DummyGatewayPlugin.process_payment(self, payment_information, previous_value)
        
        return MyMonchiqueGatewayPlugin.refund_payment(self, payment_information, previous_value)

    @require_active_plugin
    def get_supported_currencies(self, previous_value):
        config = self._get_gateway_config()
        return get_supported_currencies(config, GATEWAY_NAME)

    @require_active_plugin
    def get_client_token(self, token_config: "TokenConfig", previous_value):
        import uuid
        return str(uuid.uuid4())

    @require_active_plugin
    def get_payment_config(self, previous_value):
        config = self._get_gateway_config()
        return [{"field": "store_customer_card", "value": config.store_customer}]
