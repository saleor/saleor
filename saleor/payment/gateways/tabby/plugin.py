import logging

from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponseNotFound
from django.utils.translation import gettext_lazy as _

from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField
from saleor.plugins.models import PluginConfiguration

from ..utils import get_supported_currencies, require_active_plugin
from . import (
    GatewayConfig,
    GatewayResponse,
    PaymentData,
    capture,
    confirm_payment,
    process_payment,
    refund,
)
from .utils import handle_webhook

logger = logging.getLogger(__name__)

GATEWAY_NAME = str(_("Split in 4 interest-free payments"))


class TabbyGatewayPlugin(BasePlugin):
    PLUGIN_NAME = GATEWAY_NAME
    PLUGIN_ID = "payments.tabby"
    CONFIGURATION_PER_CHANNEL = False

    DEFAULT_CONFIGURATION = [
        {"name": "public_api_key", "value": None},
        {"name": "secret_api_key", "value": None},
        {"name": "merchant_code", "value": "wecre8"},
        {"name": "supported_currencies", "value": "SAR"},
        {"name": "webhook_header_title", "value": "Name"},
        {"name": "webhook_header_value", "value": "Tabby"},
    ]

    CONFIG_STRUCTURE = {
        "public_api_key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide Tabby public API key",
            "label": "Public API key",
        },
        "secret_api_key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide Tabby secret API key",
            "label": "Secret API key",
        },
        "webhook_header_title": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Webhook header title",
            "label": "Webhook header title",
        },
        "webhook_header_value": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Webhook header value",
            "label": "Webhook header value",
        },
        "supported_currencies": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Supported Currencies for Tabby",
            "label": "Supported Currencies",
        },
        "merchant_code": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Merchant code for tabby payment gateway",
            "label": "Merchant Code",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            auto_capture=True,
            gateway_name=GATEWAY_NAME,
            connection_params={
                "public_key": configuration["public_api_key"],
                "private_key": configuration["secret_api_key"],
                "merchant_code": configuration["merchant_code"],
                "webhook_header_value": configuration["webhook_header_value"],
                "webhook_header_title": configuration["webhook_header_title"],
            },
            supported_currencies=configuration["supported_currencies"],
        )

    def _get_gateway_config(self):
        return self.config

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct."""

        missing_fields = []
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}
        if not configuration["public_api_key"]:
            missing_fields.append("public_api_key")
        if not configuration["secret_api_key"]:
            missing_fields.append("secret_api_key")
        if not configuration["webhook_header_value"]:
            missing_fields.append("webhook_header_value")
        if not configuration["webhook_header_title"]:
            missing_fields.append("webhook_header_title")

        if plugin_configuration.active and missing_fields:
            error_msg = (
                "To enable a plugin, you need to provide values for the "
                "following fields: "
            )
            raise ValidationError(
                {
                    missing_fields[0]: ValidationError(
                        error_msg + ", ".join(missing_fields), code="invalid"
                    )
                }
            )

    def get_client_token(self):
        return self.config.connection_params.get("public_key")

    @require_active_plugin
    def get_supported_currencies(self, previous_value):
        return get_supported_currencies(self.config, self.PLUGIN_NAME)

    @require_active_plugin
    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return process_payment(payment_information, self._get_gateway_config())

    @require_active_plugin
    def capture_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return capture(payment_information, self._get_gateway_config())

    @require_active_plugin
    def refund_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return refund(payment_information, self._get_gateway_config())

    @require_active_plugin
    def confirm_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return confirm_payment(payment_information, self._get_gateway_config())

    @require_active_plugin
    def get_payment_config(self, previous_value):
        config = self._get_gateway_config()
        return [
            {"field": "api_key", "value": config.connection_params["public_key"]},
            {
                "field": "merchant_code",
                "value": config.connection_params["merchant_code"],
            },
        ]

    def webhook(self, request: HttpRequest, path: str, *args, **kwargs):
        if path == "/paid/" and request.method == "POST":
            handle_webhook(
                request=request,
                gateway=self.PLUGIN_ID,
                config=self._get_gateway_config(),
            )
            logger.info(msg=f"Finish {self.PLUGIN_ID} handling webhook")
        return HttpResponseNotFound("This path is not valid!")
