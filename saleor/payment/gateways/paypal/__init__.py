import decimal
import logging

from paypalcheckoutsdk.orders import OrdersCaptureRequest, OrdersCreateRequest
from paypalcheckoutsdk.payments import CapturesRefundRequest

from ... import TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData
from .utils import get_paypal_client

logger = logging.getLogger(__name__)


"""
Paypal API references:
https://developer.paypal.com/docs/checkout/
https://github.com/paypal/Checkout-Python-SDK
https://developer.paypal.com/docs/api/orders/v2/
https://medium.com/paypal-engineering/launch-v2-paypal-checkout-apis-45435398b987
"""


def get_client_token(**_):
    """Not implemented for Paypal gateway currently.

    The client token can be generated in the client.
    """
    pass


def get_paypal_order_id(config: GatewayConfig, amount: float, currency: str) -> str:
    """Get token (Paypal order id).

    Only for use in tests when payment has not yet been created.
    """
    client = get_paypal_client(**config.connection_params)
    request = OrdersCreateRequest()
    request.prefer("return=representation")
    request.request_body(
        {
            "intent": "CAPTURE",
            "purchase_units": [
                {"amount": {"currency_code": currency, "value": amount}}
            ],
        }
    )

    response = client.execute(request)
    return response.result.id


def authorize(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    # Currently not implemented.
    pass


def capture(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    client = get_paypal_client(**config.connection_params)
    request = OrdersCaptureRequest(payment_information.token)
    try:
        response = client.execute(request)
    except IOError as ioe:
        # Limit message length not to incur in db write error
        error_message = ioe.message[0:255]
        return GatewayResponse(
            is_success=False,
            action_required=False,
            amount=payment_information.amount,
            transaction_id=payment_information.token,
            kind=TransactionKind.CAPTURE,
            currency=payment_information.currency,
            error=error_message,
            raw_response={"IOError": error_message},
        )
    else:
        transaction = response.result.purchase_units[0].payments.captures[0]
        return GatewayResponse(
            is_success=True,
            action_required=False,
            kind=TransactionKind.CAPTURE,
            amount=decimal.Decimal(transaction.amount.value),
            currency=transaction.amount.currency_code,
            transaction_id=transaction.id,
            error=None,
        )


def void(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    """For payments that have not been captured, only authorized."""
    pass


def _build_request_body(amount: float, currency: str):
    return {"amount": {"value": amount, "currency_code": currency}}


def refund(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    # For reference, see:
    # https://github.com/paypal/Checkout-Python-SDK/blob/develop/sample/refund_order.py
    # Warning: in sandbox mode, refunds can be rejected for unclear reasons by the
    # Paypal Api.
    client = get_paypal_client(**config.connection_params)
    request = CapturesRefundRequest(payment_information.token)
    request.prefer("return=representation")
    request.request_body(
        _build_request_body(
            float(payment_information.amount), payment_information.currency
        )
    )
    try:
        response = client.execute(request)
    except IOError as ioe:
        # Limit message length not to incur in db write error
        error_message = ioe.message[0:255]
        return GatewayResponse(
            is_success=False,
            action_required=False,
            amount=payment_information.amount,
            transaction_id=payment_information.token,
            kind=TransactionKind.REFUND,
            currency=payment_information.currency,
            error=error_message,
            raw_response={"IOError": error_message},
        )
    else:
        return GatewayResponse(
            is_success=True,
            action_required=False,
            amount=decimal.Decimal(response.result.amount.value),
            transaction_id=response.result.id,
            kind=TransactionKind.REFUND,
            currency=response.result.amount.currency_code,
            error=None,
        )


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    return capture(payment_information, config)
