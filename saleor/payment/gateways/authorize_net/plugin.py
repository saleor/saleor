from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError

from saleor.account.models import User
from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField
from saleor.plugins.error_codes import PluginErrorCode

from ... import PaymentError
from ...models import Payment
from ..utils import get_supported_currencies
from . import (
    GatewayConfig,
    authenticate_test,
    authorize,
    capture,
    list_client_sources,
    process_payment,
    refund,
    void,
)

GATEWAY_NAME = "Authorize.Net"

if TYPE_CHECKING:
    from ...interface import CustomerSource
    from ..models import PluginConfiguration
    from . import GatewayResponse, PaymentData


class AuthorizeNetGatewayPlugin(BasePlugin):
    PLUGIN_NAME = GATEWAY_NAME
    PLUGIN_ID = "mirumee.payments.authorize_net"
    CONFIGURATION_PER_CHANNEL = True

    DEFAULT_CONFIGURATION = [
        {"name": "api_login_id", "value": None},
        {"name": "transaction_key", "value": None},
        {"name": "client_key", "value": None},
        {"name": "use_sandbox", "value": True},
        {"name": "store_customers_card", "value": False},
        {"name": "automatic_payment_capture", "value": True},
        {"name": "supported_currencies", "value": ""},
    ]

    CONFIG_STRUCTURE = {
        "api_login_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Provide public Authorize.Net Login ID.",
            "label": "API Login ID",
        },
        "transaction_key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide private Authorize.Net Transaction Key.",
            "label": "Transaction Key",
        },
        "client_key": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Provide public Authorize.Net Client Key.",
            "label": "Client Key",
        },
        "use_sandbox": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": (
                "Determines if Saleor should use Authorize.Net sandbox environment."
            ),
            "label": "Use sandbox",
        },
        "store_customers_card": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should store cards on payments "
            "in Stripe customer.",
            "label": "Store customers card",
        },
        "automatic_payment_capture": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should automatically capture payments.",
            "label": "Automatic payment capture",
        },
        "supported_currencies": {
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
            auto_capture=configuration["automatic_payment_capture"],
            supported_currencies=configuration["supported_currencies"],
            connection_params={
                "api_login_id": configuration["api_login_id"],
                "transaction_key": configuration["transaction_key"],
                "client_key": configuration["client_key"],
                "use_sandbox": configuration["use_sandbox"],
            },
            store_customer=configuration["store_customers_card"],
        )

    def _get_gateway_config(self) -> GatewayConfig:
        return self.config

    @classmethod
    def validate_plugin_configuration(
        cls, plugin_configuration: "PluginConfiguration", **kwargs
    ):
        """Validate if provided configuration is correct."""
        configuration = {
            item["name"]: item["value"] for item in plugin_configuration.configuration
        }

        api_login_id = configuration.get("api_login_id", None)
        transaction_key = configuration.get("transaction_key", None)

        # Only check when active and both credentials are set
        # Otherwise the dashboard is hard to use
        if plugin_configuration.active and api_login_id and transaction_key:
            use_sandbox = True if configuration.get("use_sandbox") else False
            success, message = authenticate_test(
                api_login_id, transaction_key, use_sandbox
            )
            if not success:
                raise ValidationError(
                    {
                        "api_login_id": ValidationError(
                            message,
                            code=PluginErrorCode.PLUGIN_MISCONFIGURED.value,
                        ),
                        "transaction_key": ValidationError(
                            message,
                            code=PluginErrorCode.PLUGIN_MISCONFIGURED.value,
                        ),
                    }
                )

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
        try:
            payment = Payment.objects.get(pk=payment_information.payment_id)
        except Payment.DoesNotExist:
            raise PaymentError(f"Cannot find Payment {payment_information.payment_id}.")
        return refund(
            payment_information, payment.cc_last_digits, self._get_gateway_config()
        )

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
        user = User.objects.filter(
            checkouts__payments__id=payment_information.payment_id
        ).first()
        user_id = user.id if user else None
        return process_payment(payment_information, self._get_gateway_config(), user_id)

    def list_payment_sources(
        self, customer_id: str, previous_value
    ) -> list["CustomerSource"]:
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
            {
                "field": "api_login_id",
                "value": config.connection_params["api_login_id"],
            },
            {"field": "client_key", "value": config.connection_params["client_key"]},
            {"field": "use_sandbox", "value": config.connection_params["use_sandbox"]},
            {"field": "store_customer_card", "value": config.store_customer},
        ]
