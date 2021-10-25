from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError

from ....order.models import Fulfillment
from ....plugins.base_plugin import BasePlugin, ConfigurationTypeField
from ....plugins.error_codes import PluginErrorCode
from . import (
    GatewayConfig,
    api,
    capture,
    get_api_config,
    process_payment,
    refund,
    tracking_number_updated,
    void,
)
from .const import (
    FILL_MISSING_ADDRESS,
    MERCHANT_CODE,
    SHIPPING_COMPANY,
    SHIPPING_COMPANY_CODES,
    SP_CODE,
    TERMINAL_ID,
    USE_SANDBOX,
)
from .utils import np_atobarai_opentracing_trace

GATEWAY_NAME = "NP後払い"

if TYPE_CHECKING:
    # flake8: noqa
    from ....plugins.models import PluginConfiguration
    from . import GatewayResponse, PaymentData


class NPAtobaraiGatewayPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.payments.np-atobarai"
    PLUGIN_NAME = GATEWAY_NAME
    CONFIGURATION_PER_CHANNEL = True
    SUPPORTED_CURRENCIES = "JPY"

    DEFAULT_CONFIGURATION = [
        {"name": MERCHANT_CODE, "value": None},
        {"name": SP_CODE, "value": None},
        {"name": TERMINAL_ID, "value": None},
        {"name": USE_SANDBOX, "value": True},
        {"name": FILL_MISSING_ADDRESS, "value": True},
        {"name": SHIPPING_COMPANY, "value": "50000"},
    ]

    CONFIG_STRUCTURE = {
        MERCHANT_CODE: {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide NP後払い Merchant Code.",
            "label": "Merchant Code",
        },
        SP_CODE: {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide NP後払い SP Code.",
            "label": "SP Code",
        },
        TERMINAL_ID: {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide NP後払い Terminal ID.",
            "label": "Terminal ID",
        },
        USE_SANDBOX: {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should use NP後払い sandbox API.",
            "label": "Use sandbox",
        },
        FILL_MISSING_ADDRESS: {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": (
                "Determines if Saleor should generate missing "
                "AddressData.city and AddressData.city_area"
            ),
            "label": "Fill missing address",
        },
        SHIPPING_COMPANY: {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Determines shipping company used in fulfillment report.",
            "label": "Shipping company",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            auto_capture=False,
            supported_currencies=self.SUPPORTED_CURRENCIES,
            connection_params={
                MERCHANT_CODE: configuration[MERCHANT_CODE],
                SP_CODE: configuration[SP_CODE],
                TERMINAL_ID: configuration[TERMINAL_ID],
                USE_SANDBOX: configuration[USE_SANDBOX],
                FILL_MISSING_ADDRESS: configuration[FILL_MISSING_ADDRESS],
                SHIPPING_COMPANY: configuration[SHIPPING_COMPANY],
            },
        )

    def _get_gateway_config(self) -> GatewayConfig:
        return self.config

    def capture_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return capture(payment_information, self._get_gateway_config())

    def refund_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return refund(payment_information, self._get_gateway_config())

    def void_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return void(payment_information, self._get_gateway_config())

    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return process_payment(payment_information, self._get_gateway_config())

    def tracking_number_updated(self, fulfillment: "Fulfillment", previous_value):
        tracking_number_updated(fulfillment, self._get_gateway_config())

    def get_supported_currencies(self, previous_value):
        return self.SUPPORTED_CURRENCIES

    def token_is_required_as_payment_input(self, previous_value):
        return False

    @classmethod
    def validate_authentication(cls, plugin_configuration: "PluginConfiguration"):
        conf = {
            data["name"]: data["value"] for data in plugin_configuration.configuration
        }
        with np_atobarai_opentracing_trace("np-atobarai.utilities.ping"):
            response = api.health_check(get_api_config(conf))

        if not response:
            raise ValidationError(
                {
                    field: ValidationError(
                        "Authentication failed. Please check provided data.",
                        code=PluginErrorCode.PLUGIN_MISCONFIGURED.value,
                    )
                    for field in [MERCHANT_CODE, SP_CODE, TERMINAL_ID]
                }
            )

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct."""
        if not plugin_configuration.active:
            return

        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}
        missing_fields = [
            field
            for field in [MERCHANT_CODE, SP_CODE, TERMINAL_ID, SHIPPING_COMPANY]
            if not configuration[field]
        ]

        if plugin_configuration.active:
            if missing_fields:
                raise ValidationError(
                    {
                        field: ValidationError(
                            f"The parameter is required.",
                            code=PluginErrorCode.REQUIRED.value,
                        )
                        for field in missing_fields
                    }
                )
            if configuration[SHIPPING_COMPANY] not in SHIPPING_COMPANY_CODES:
                raise ValidationError(
                    {
                        SHIPPING_COMPANY: ValidationError(
                            f"Shipping company code is invalid",
                            code=PluginErrorCode.INVALID.value,
                        )
                    }
                )

            cls.validate_authentication(plugin_configuration)

    def get_payment_config(self, previous_value):
        return []
