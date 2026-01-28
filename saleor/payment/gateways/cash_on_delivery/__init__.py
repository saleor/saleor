import uuid

from ... import ChargeStatus, TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData, PaymentMethodInfo


GATEWAY_NAME = "Cash on Delivery"


def get_client_token(**_):
    """Return client token for Cash on Delivery.

    COD doesn't need a token, but we return a UUID for consistency.
    """
    return str(uuid.uuid4())


def authorize(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Authorize payment for Cash on Delivery.

    For COD, authorization always succeeds as payment will be collected on delivery.
    """
    return GatewayResponse(
        is_success=True,
        action_required=False,
        kind=TransactionKind.AUTH,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token or str(uuid.uuid4()),
        error=None,
        payment_method_info=PaymentMethodInfo(
            type="cash_on_delivery",
            brand="COD",
            name="Cash on Delivery",
        ),
    )


def capture(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Capture payment for Cash on Delivery.

    This is called when the order is marked as delivered/paid.
    """
    return GatewayResponse(
        is_success=True,
        action_required=False,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token or str(uuid.uuid4()),
        error=None,
        payment_method_info=PaymentMethodInfo(
            type="cash_on_delivery",
            brand="COD",
            name="Cash on Delivery",
        ),
    )


def confirm(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Confirm payment for Cash on Delivery."""
    return GatewayResponse(
        is_success=True,
        action_required=False,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token or str(uuid.uuid4()),
        error=None,
    )


def void(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Void (cancel) a Cash on Delivery payment."""
    return GatewayResponse(
        is_success=True,
        action_required=False,
        kind=TransactionKind.VOID,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token or str(uuid.uuid4()),
        error=None,
    )


def refund(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Refund a Cash on Delivery payment."""
    return GatewayResponse(
        is_success=True,
        action_required=False,
        kind=TransactionKind.REFUND,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token or str(uuid.uuid4()),
        error=None,
    )


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Process Cash on Delivery payment.

    For COD, we authorize the payment immediately. The actual capture happens
    when the order is delivered and payment is collected.
    """
    # For COD, we authorize first (payment will be captured on delivery)
    return authorize(payment_information, config)
