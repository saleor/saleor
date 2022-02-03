import json
import logging
import os

import requests
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponseNotFound, JsonResponse
from django.utils.translation import gettext_lazy as _

from saleor.graphql.core.enums import PluginErrorCode
from saleor.payment.gateways.adyen.utils.apple_pay import (
    validate_payment_data_for_apple_pay,
)
from saleor.payment.gateways.utils import (
    get_supported_currencies,
    require_active_plugin,
)
from saleor.payment.interface import GatewayResponse, PaymentData
from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField
from saleor.plugins.models import PluginConfiguration

from . import GatewayConfig, capture, confirm_payment, process_payment, refund
from .utils import handle_webhook

GATEWAY_NAME = str(_("Credit Card"))

logger = logging.getLogger(__name__)


class CheckoutGatewayPlugin(BasePlugin):
    PLUGIN_NAME = GATEWAY_NAME
    PLUGIN_ID = "payments.checkout"
    CONFIGURATION_PER_CHANNEL = False

    DEFAULT_CONFIGURATION = [
        {"name": "use_sandbox", "value": True},
        {"name": "public_api_key", "value": None},
        {"name": "secret_api_key", "value": None},
        {"name": "supported_currencies", "value": "SAR"},
    ]

    CONFIG_STRUCTURE = {
        "public_api_key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide  public API key",
            "label": "Public API key",
        },
        "secret_api_key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide Checkout secret API key",
            "label": "Secret API key",
        },
        "use_sandbox": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Sandbox variable used for testing environment.",
            "label": "Sandbox",
        },
        "supported_currencies": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Supported Currencies for Checkout",
            "label": "Supported Currencies",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            auto_capture=True,
            gateway_name=GATEWAY_NAME,
            connection_params={
                "sandbox": configuration["use_sandbox"],
                "public_key": configuration["public_api_key"],
                "private_key": configuration["secret_api_key"],
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

        if plugin_configuration.active and missing_fields:
            error_msg = (
                "To enable a plugin, you need to provide values for the "
                "following fields: "
            )
            raise ValidationError(
                {
                    f"{field}": ValidationError(
                        error_msg.format(field),
                        code=PluginErrorCode.PLUGIN_MISCONFIGURED.value,
                    )
                    for field in missing_fields
                },
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
        return process_payment(
            payment_information=payment_information, config=self._get_gateway_config()
        )

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
        return [{"field": "api_key", "value": config.connection_params["public_key"]}]

    def webhook(self, request: HttpRequest, path: str, *args, **kwargs):
        if path == "/paid/" and request.method == "POST":
            response = handle_webhook(
                request=request,
                gateway=self.PLUGIN_ID,
                config=self._get_gateway_config(),
            )
            logger.info(msg="Finish handling webhook")
            return response
        elif path == "/apple-pay/validate-/" and request.method == "POST":
            # Apple Pay session
            payment_data = json.loads(request.body.decode("utf-8").replace("'", '"'))
            display_name = payment_data.get("displayName", "")
            validation_url = payment_data.get("validationUrl", "")
            initiative_context = payment_data.get("initiativeContext", "")
            merchant_identifier = payment_data.get("merchantIdentifier", "")

            payment_data = {
                "initiative": "web",
                "displayName": display_name,
                "validationUrl": validation_url,
                "initiativeContext": initiative_context,
                "merchantIdentifier": merchant_identifier,
            }
            validate_payment_data_for_apple_pay(
                certificate="certificate",
                domain=initiative_context,
                display_name=display_name,
                validation_url=validation_url,
                merchant_identifier=merchant_identifier,
            )
            cwd = os.path.join(os.path.dirname(__file__))
            response = requests.post(
                validation_url,
                json=payment_data,
                cert=(
                    cwd + "/certificate_sandbox.pem",
                    cwd + "/certificate_sandbox.key",
                ),
            )
            logger.info(msg="Finish validating Apple Pay session")
            return JsonResponse(data=response.json(), status=response.status_code)

        return HttpResponseNotFound("This path is not valid!")
