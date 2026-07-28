"""Fake payment gateway driving the legacy, plugin-based `Payment` flow in tests.

It is not part of the shipped plugin set (`settings.BUILTIN_PLUGINS`) and has to be
enabled explicitly through `settings.PLUGINS`.

The gateway succeeds by default. Two hooks make it fail on demand:

- monkeypatching `dummy_success` to return `False` fails any operation, and
- a payment token listed in `TOKEN_VALIDATION_MAPPING` fails the capture with the
  mapped message, which simulates a card rejected by the provider.
"""

import uuid

from saleor.payment import ChargeStatus, TransactionKind
from saleor.payment.gateways.utils import get_supported_currencies
from saleor.payment.interface import (
    GatewayConfig,
    GatewayResponse,
    PaymentData,
    PaymentMethodInfo,
    TokenConfig,
)
from saleor.plugins.base_plugin import BasePlugin

GATEWAY_NAME = "Dummy"

TOKEN_EXPIRED = "0069"
TOKEN_INSUFFICIENT_FUNDS = "9995"
TOKEN_INCORRECT_CVV = "0127"
TOKEN_DECLINE = "0002"

TOKEN_VALIDATION_MAPPING = {
    TOKEN_EXPIRED: "Card expired",
    TOKEN_INSUFFICIENT_FUNDS: "Insufficient funds",
    TOKEN_INCORRECT_CVV: "Incorrect CVV",
    TOKEN_DECLINE: "Card declined",
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
    if not error and not dummy_success():
        error = "Unable to process capture"

    return GatewayResponse(
        is_success=not error,
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
    """Process the payment.

    A payment token holding a `ChargeStatus` value drives the payment to that status;
    anything else is captured straight away.
    """
    token = payment_information.token

    if token not in dict(ChargeStatus.CHOICES):
        return capture(payment_information, config)

    charge_status = token
    authorize_response = authorize(payment_information, config)
    if charge_status == ChargeStatus.NOT_CHARGED or not config.auto_capture:
        return authorize_response

    capture_response = capture(payment_information, config)
    if charge_status == ChargeStatus.FULLY_REFUNDED:
        return refund(payment_information, config)
    return capture_response


class DummyGatewayPlugin(BasePlugin):
    """Fake payment gateway plugin. See the module docstring."""

    PLUGIN_ID = "mirumee.payments.dummy"
    PLUGIN_NAME = GATEWAY_NAME
    DEFAULT_ACTIVE = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            auto_capture=True,
            supported_currencies="USD, PLN",
            connection_params={},
            store_customer=False,
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
