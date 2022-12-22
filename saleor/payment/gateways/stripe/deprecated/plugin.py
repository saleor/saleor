from typing import TYPE_CHECKING, List

from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField

from ...utils import get_supported_currencies
from . import (
    GatewayConfig,
    authorize,
    capture,
    list_client_sources,
    process_payment,
    refund,
    void,
)

GATEWAY_NAME = "Stripe (Deprecated)"

if TYPE_CHECKING:
    from ....interface import CustomerSource
    from . import GatewayResponse, PaymentData


class DeprecatedStripeGatewayPlugin(BasePlugin):
    PLUGIN_NAME = GATEWAY_NAME
    PLUGIN_ID = "mirumee.payments.stripe"
    PLUGIN_DESCRIPTION = """
    This plugin will be removed in Saleor 4.0. Use the new Stripe plugin which
    implements webhook support, 3D Secure and SCA.
    """

    DEFAULT_CONFIGURATION = [
        {"name": "Public API key", "value": None},
        {"name": "Secret API key", "value": None},
        {"name": "Store customers card", "value": False},
        {"name": "Automatic payment capture", "value": True},
        {"name": "Supported currencies", "value": ""},
    ]

    CONFIG_STRUCTURE = {
        "Public API key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide Stripe public API key.",
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
            "help_text": "Determines if Saleor should automatically capture payments.",
            "label": "Automatic payment capture",
        },
        "Supported currencies": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Determines currencies supported by gateway."
            " Please enter currency codes separated by a comma.",
            "label": "Supported currencies",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            auto_capture=configuration["Automatic payment capture"],
            supported_currencies=configuration["Supported currencies"],
            connection_params={
                "public_key": configuration["Public API key"],
                "private_key": configuration["Secret API key"],
            },
            store_customer=configuration["Store customers card"],
        )

    def _get_gateway_config(self):
        return self.config

    def authorize_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        if not self.active:
            return previous_value
        return authorize(payment_information, self._get_gateway_config())

    def capture_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        if not self.active:
            return previous_value
        return capture(payment_information, self._get_gateway_config())

    def refund_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        if not self.active:
            return previous_value
        return refund(payment_information, self._get_gateway_config())

    def void_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        if not self.active:
            return previous_value
        return void(payment_information, self._get_gateway_config())

    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        if not self.active:
            return previous_value
        return process_payment(payment_information, self._get_gateway_config())

    def list_payment_sources(
        self, customer_id: str, previous_value
    ) -> List["CustomerSource"]:
        if not self.active:
            return previous_value
        sources = list_client_sources(self._get_gateway_config(), customer_id)
        previous_value.extend(sources)
        return previous_value

    def get_supported_currencies(self, previous_value):
        if not self.active:
            return previous_value
        config = self._get_gateway_config()
        return get_supported_currencies(config, GATEWAY_NAME)

    def get_payment_config(self, previous_value):
        if not self.active:
            return previous_value
        config = self._get_gateway_config()
        return [
            {"field": "api_key", "value": config.connection_params["public_key"]},
            {"field": "store_customer_card", "value": config.store_customer},
        ]
