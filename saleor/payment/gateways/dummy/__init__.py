import uuid
from typing import Optional

from ... import TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData

PREAUTHORIZED_TOKENS = ["4111111111111111", "4111111111111112"]

TOKEN_VALIDATION_MAPPING = {
    "4000000000000069": "Card expired",
    "4000000000009995": "Insufficient funds",
    "4000000000000127": "Incorrect csv",
    "4000000000000002": "Card declined",
    "4111111111111111": "Card declined",
}


def dummy_success():
    return True


def validate_token(token: Optional[str]):
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
        transaction_id=payment_information.token,
        error=error,
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
        transaction_id=payment_information.token,
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
        transaction_id=payment_information.token,
        error=error,
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
        transaction_id=payment_information.token,
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
        transaction_id=payment_information.token,
        error=error,
    )


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Process the payment."""
    token = payment_information.token

    if token in PREAUTHORIZED_TOKENS and not config.auto_capture:
        return authorize(payment_information, config)

    return capture(payment_information, config)
