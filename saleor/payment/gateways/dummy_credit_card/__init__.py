import uuid
from typing import Optional

from ... import TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData, PaymentMethodInfo

TOKEN_PREAUTHORIZE_SUCCESS = "4111111111111112"
TOKEN_PREAUTHORIZE_DECLINE = "4111111111111111"
TOKEN_EXPIRED = "4000000000000069"
TOKEN_INSUFFICIENT_FUNDS = "4000000000009995"
TOKEN_INCORRECT_CVV = "4000000000000127"
TOKEN_DECLINE = "4000000000000002"

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
