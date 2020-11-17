from typing import List

from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField

from ..utils import get_supported_currencies
from . import GatewayConfig, process_payment


GATEWAY_NAME = "Authorize.Net"


def require_active_plugin(fn):
    def wrapped(self, *args, **kwargs):
        previous = kwargs.get("previous_value", None)
        if not self.active:
            return previous
        return fn(self, *args, **kwargs)

    return wrapped


class AuthorizeNetGatewayPlugin(BasePlugin):
    PLUGIN_NAME = GATEWAY_NAME
    PLUGIN_ID = "mirumee.payments.authorize_net"

    DEFAULT_CONFIGURATION = [
        {"name": "api_login_id", "value": None},
        {"name": "transaction_key", "value": None},
        {"name": "client_key", "value": None},
    ]

    CONFIG_STRUCTURE = {
        "api_login_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": ("Provide public Authorize.Net Login ID."),
            "label": "API Login ID",
        },
        "transaction_key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": ("Provide private Authorize.Net Transaction Key."),
            "label": "Transaction Key",
        },
        "client_key": {
            "type": ConfigurationTypeField.STRING,
            "help_text": ("Provide public Authorize.Net Client Key"),
            "label": "Client Key",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            auto_capture=True,
            supported_currencies="USD",
            # auto_capture=configuration["Automatic payment capture"],
            # supported_currencies=configuration["Supported currencies"],
            connection_params={
                "api_login_id": configuration["api_login_id"],
                "transaction_key": configuration["transaction_key"],
                "client_key": configuration["client_key"],
            },
            # store_customer=configuration["Store customers card"],
        )

    def _get_gateway_config(self) -> GatewayConfig:
        return self.config

    # @require_active_plugin
    # def authorize_payment(
    #     self, payment_information: "PaymentData", previous_value
    # ) -> "GatewayResponse":
    #     pass
    # return authorize(payment_information, self._get_gateway_config())

    @require_active_plugin
    def capture_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        pass  # return capture(payment_information, self._get_gateway_config())

    @require_active_plugin
    def refund_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        pass  # return refund(payment_information, self._get_gateway_config())

    @require_active_plugin
    def void_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        pass  # return void(payment_information, self._get_gateway_config())

    @require_active_plugin
    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return process_payment(payment_information, self._get_gateway_config())

    @require_active_plugin
    def list_payment_sources(
        self, customer_id: str, previous_value
    ) -> List["CustomerSource"]:
        pass
        # sources = list_client_sources(self._get_gateway_config(), customer_id)
        # previous_value.extend(sources)
        # return previous_value

    @require_active_plugin
    def get_supported_currencies(self, previous_value):
        config = self._get_gateway_config()
        return get_supported_currencies(config, GATEWAY_NAME)

    @require_active_plugin
    def get_payment_config(self, previous_value):
        config = self._get_gateway_config()
        return [
            {
                "field": "api_login_id",
                "value": config.connection_params["api_login_id"],
            },
            {"field": "client_key", "value": config.connection_params["client_key"]},
        ]
