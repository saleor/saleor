from ... import TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData


def authorize(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Perform authorize transaction."""

    return GatewayResponse(
        error=None,
        is_success=True,
        action_required=False,
        kind=TransactionKind.AUTH,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=str(payment_information.token),
    )


def void(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    """Perform void transaction."""

    return GatewayResponse(
        error=None,
        is_success=True,
        action_required=False,
        kind=TransactionKind.VOID,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=str(payment_information.token),
    )


def capture(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    """Perform capture transaction."""

    return GatewayResponse(
        error=None,
        is_success=True,
        action_required=False,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=str(payment_information.token),
    )


def confirm(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    """Perform confirm transaction."""

    return GatewayResponse(
        error=None,
        is_success=True,
        action_required=False,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=str(payment_information.currency),
        transaction_id=str(payment_information.token),
    )


def refund(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    return GatewayResponse(
        error=None,
        is_success=True,
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
