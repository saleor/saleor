import uuid

from ... import TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData


def cash_success():
    return True


def get_client_token(**_):
    return str(uuid.uuid4())


def authorize(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    success = cash_success()
    error = None
    if not success:
        error = "Unable to authorize transaction"
    return GatewayResponse(
        error=error,
        is_success=success,
        action_required=False,
        kind=TransactionKind.AUTH,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=str(payment_information.token),
    )


def void(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    error = None
    success = cash_success()
    if not success:
        error = "Unable to void the transaction."
    return GatewayResponse(
        error=error,
        is_success=success,
        action_required=False,
        kind=TransactionKind.VOID,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=str(payment_information.token),
    )


def capture(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    """Perform capture transaction."""
    error = None
    success = cash_success()
    if not success:
        error = "Unable to process capture"

    return GatewayResponse(
        error=error,
        is_success=success,
        action_required=False,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=str(payment_information.token),
    )


def confirm(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    """Perform confirm transaction."""
    error = None
    success = cash_success()
    if not success:
        error = "Unable to process capture"

    return GatewayResponse(
        error=error,
        is_success=success,
        action_required=False,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=str(payment_information.currency),
        transaction_id=str(payment_information.token),
    )


def refund(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    error = None
    success = cash_success()
    if not success:
        error = "Unable to process refund"
    return GatewayResponse(
        error=error,
        is_success=success,
        action_required=False,
        kind=TransactionKind.REFUND,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=str(payment_information.token),
    )


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Process the payment."""
    return authorize(payment_information, config)
