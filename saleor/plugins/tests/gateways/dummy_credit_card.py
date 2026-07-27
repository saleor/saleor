import uuid

from saleor.payment import TransactionKind
from saleor.payment.gateways.utils import get_supported_currencies
from saleor.payment.interface import (
    GatewayConfig,
    GatewayResponse,
    PaymentData,
    PaymentMethodInfo,
    TokenConfig,
)
from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField

GATEWAY_NAME = "Dummy Credit Card"

TOKEN_PREAUTHORIZE_SUCCESS = "1112"
TOKEN_PREAUTHORIZE_DECLINE = "1111"
TOKEN_EXPIRED = "0069"
TOKEN_INSUFFICIENT_FUNDS = "9995"
TOKEN_INCORRECT_CVV = "0127"
TOKEN_DECLINE = "0002"

PREAUTHORIZED_TOKENS = [TOKEN_PREAUTHORIZE_DECLINE, TOKEN_PREAUTHORIZE_SUCCESS]

TOKEN_VALIDATION_MAPPING = {
    TOKEN_EXPIRED: "Card expired",
    TOKEN_INSUFFICIENT_FUNDS: "Insufficient funds",
    TOKEN_INCORRECT_CVV: "Incorrect CVV",
    TOKEN_DECLINE: "Card declined",
    TOKEN_PREAUTHORIZE_DECLINE: "Card declined",
}


def dummy_success():
    return True


def validate_token(token: str | None):
    return TOKEN_VALIDATION_MAPPING.get(token, None) if token else None


def get_client_token(**_):
    return str(uuid.uuid4())


def authorize(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    success = dummy_success()
    error = None
    if not success:
        error = "Unable to authorize transaction"
    return GatewayResponse(
        is_success=success,
        action_required=False,
        kind=TransactionKind.AUTH,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token or "",
        error=error,
        payment_method_info=PaymentMethodInfo(
            last_4="1234",
            exp_year=2222,
            exp_month=12,
            brand="dummy_visa",
            name="Holder name",
            type="card",
        ),
    )


def void(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    error = None
    success = dummy_success()
    if not success:
        error = "Unable to void the transaction."
    return GatewayResponse(
        is_success=success,
        action_required=False,
        kind=TransactionKind.VOID,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token or "",
        error=error,
    )


def capture(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    """Perform capture transaction."""
    error = validate_token(payment_information.token)
    success = not error

    return GatewayResponse(
        is_success=success,
        action_required=False,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token or "",
        error=error,
        payment_method_info=PaymentMethodInfo(
            last_4="1234",
            exp_year=2222,
            exp_month=12,
            brand="dummy_visa",
            name="Holder name",
            type="card",
        ),
    )


def confirm(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    """Perform confirm transaction."""
    error = None
    success = dummy_success()
    if not success:
        error = "Unable to process capture"

    return GatewayResponse(
        is_success=success,
        action_required=False,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token or "",
        error=error,
    )


def refund(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    error = None
    success = dummy_success()
    if not success:
        error = "Unable to process refund"
    return GatewayResponse(
        is_success=success,
        action_required=False,
        kind=TransactionKind.REFUND,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token or "",
        error=error,
    )


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Process the payment."""
    token = payment_information.token

    if token in PREAUTHORIZED_TOKENS:
        authorize_response = authorize(payment_information, config)
        if not config.auto_capture:
            return authorize_response

    return capture(payment_information, config)


class DummyCreditCardGatewayPlugin(BasePlugin):
    """Fake payment gateway used only by the test suite.

    It is not part of the shipped plugin set and must be enabled explicitly
    through ``settings.PLUGINS`` in tests.
    """

    PLUGIN_ID = "mirumee.payments.dummy_credit_card"
    PLUGIN_NAME = GATEWAY_NAME
    DEFAULT_ACTIVE = False
    DEFAULT_CONFIGURATION = [
        {"name": "Store customers card", "value": False},
        {"name": "Automatic payment capture", "value": True},
        {"name": "Supported currencies", "value": "USD, PLN"},
    ]
    CONFIG_STRUCTURE = {
        "Store customers card": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should store cards.",
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
            connection_params={},
            store_customer=configuration["Store customers card"],
        )

    def _get_gateway_config(self):
        return self.config

    def authorize_payment(
        self, payment_information: PaymentData, previous_value
    ) -> GatewayResponse:
        if not self.active:
            return previous_value
        return authorize(payment_information, self._get_gateway_config())

    def capture_payment(
        self, payment_information: PaymentData, previous_value
    ) -> GatewayResponse:
        if not self.active:
            return previous_value
        return capture(payment_information, self._get_gateway_config())

    def confirm_payment(
        self, payment_information: PaymentData, previous_value
    ) -> GatewayResponse:
        if not self.active:
            return previous_value
        return confirm(payment_information, self._get_gateway_config())

    def refund_payment(
        self, payment_information: PaymentData, previous_value
    ) -> GatewayResponse:
        if not self.active:
            return previous_value
        return refund(payment_information, self._get_gateway_config())

    def void_payment(
        self, payment_information: PaymentData, previous_value
    ) -> GatewayResponse:
        if not self.active:
            return previous_value
        return void(payment_information, self._get_gateway_config())

    def process_payment(
        self, payment_information: PaymentData, previous_value
    ) -> GatewayResponse:
        if not self.active:
            return previous_value
        return process_payment(payment_information, self._get_gateway_config())

    def get_client_token(self, token_config: TokenConfig, previous_value):
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
        config = self._get_gateway_config()
        return [{"field": "store_customer_card", "value": config.store_customer}]
