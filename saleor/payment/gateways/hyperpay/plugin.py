"""HyperPay payment gateway plugin."""

from typing import TYPE_CHECKING

from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField

from ..utils import get_supported_currencies
from . import (
    GATEWAY_NAME,
    GatewayConfig,
    authorize,
    capture,
    confirm,
    get_client_token,
    process_payment,
    refund,
    void,
)
from .consts import (
    DEFAULT_PAYMENT_BRANDS,
    DEFAULT_SUPPORTED_CURRENCIES,
    PLUGIN_DESCRIPTION,
    PLUGIN_ID,
    PLUGIN_NAME,
)

if TYPE_CHECKING:
    from ...interface import GatewayResponse, PaymentData, TokenConfig


class HyperPayGatewayPlugin(BasePlugin):
    """HyperPay payment gateway plugin.

    This plugin integrates HyperPay payment gateway with Saleor,
    supporting credit cards, debit cards, MADA, and other payment methods
    available in the MENA region.
    """

    PLUGIN_ID = PLUGIN_ID
    PLUGIN_NAME = PLUGIN_NAME
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = PLUGIN_DESCRIPTION
    DEFAULT_CONFIGURATION = [
        {"name": "Entity ID", "value": ""},
        {"name": "Access Token", "value": ""},
        {"name": "Test mode", "value": True},
        {"name": "Payment brands", "value": DEFAULT_PAYMENT_BRANDS},
        {"name": "Automatic payment capture", "value": True},
        {"name": "Supported currencies", "value": DEFAULT_SUPPORTED_CURRENCIES},
    ]
    CONFIG_STRUCTURE = {
        "Entity ID": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Your HyperPay Entity ID (provided by HyperPay).",
            "label": "Entity ID",
        },
        "Access Token": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Your HyperPay Access Token (provided by HyperPay).",
            "label": "Access Token",
        },
        "Test mode": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": (
                "Enable test mode to use HyperPay sandbox environment. "
                "Disable for production."
            ),
            "label": "Test mode",
        },
        "Payment brands": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "Space-separated list of payment brands to accept. "
                "Examples: VISA, MASTER, MADA, AMEX, APPLEPAY"
            ),
            "label": "Payment brands",
        },
        "Automatic payment capture": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": (
                "If enabled, payments are captured immediately. "
                "If disabled, payments are pre-authorized and must be captured later."
            ),
            "label": "Automatic payment capture",
        },
        "Supported currencies": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "Comma-separated list of supported currency codes. "
                "Example: SAR, AED, USD, EUR"
            ),
            "label": "Supported currencies",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            auto_capture=configuration.get("Automatic payment capture", True),
            supported_currencies=configuration.get(
                "Supported currencies", DEFAULT_SUPPORTED_CURRENCIES
            ),
            connection_params={
                "entity_id": configuration.get("Entity ID", ""),
                "access_token": configuration.get("Access Token", ""),
                "test_mode": configuration.get("Test mode", True),
                "payment_brands": configuration.get(
                    "Payment brands", DEFAULT_PAYMENT_BRANDS
                ),
            },
            store_customer=False,
        )

    def _get_gateway_config(self) -> GatewayConfig:
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

    def confirm_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        if not self.active:
            return previous_value
        return confirm(payment_information, self._get_gateway_config())

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

    def get_client_token(self, token_config: "TokenConfig", previous_value):
        if not self.active:
            return previous_value
        return get_client_token()

    def get_supported_currencies(self, previous_value):
        if not self.active:
            return previous_value
        config = self._get_gateway_config()
        return get_supported_currencies(config, GATEWAY_NAME)

    def get_payment_config(self, previous_value):
        if not self.active:
            return previous_value
        return [
            {"field": "store_customer_card", "value": False},
            {"field": "test_mode", "value": self.config.connection_params.get("test_mode", True)},
        ]

    def token_is_required_as_payment_input(self, previous_value):
        """Token is required for HyperPay (checkout ID from prepare_checkout)."""
        if not self.active:
            return previous_value
        return True
