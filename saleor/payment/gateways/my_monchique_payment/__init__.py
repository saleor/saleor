import json
from typing import Any, Dict, List, Optional, Tuple, Union

from lxml.objectify import ObjectifiedElement

from ... import TransactionKind
from ....core.auth_backend import JSONWebTokenBackend
from ....payment.interface import (
    CustomerSource,
    GatewayConfig,
    GatewayResponse,
    PaymentData,
    PaymentMethodInfo,
)
from ....monchique.network import payment_authorize, payment_capture, payment_refund
from ...models import (MonchiquePayment, Payment)

def authorize(
    payment_information: PaymentData,
    config: GatewayConfig,
    user_id: Optional[int] = None,
) -> GatewayResponse:
    backend = JSONWebTokenBackend()
    user = backend.get_user(payment_information.customer_email)
    authorization_response = payment_authorize(payment_information.amount, user.monchique_token)

    is_success = authorization_response['is_authorized']
    transaction_id = authorization_response.get('tx_id')

    if is_success:
        payment = Payment.objects.get(pk=payment_information.payment_id)
        obj = MonchiquePayment.objects.create(payment_id=payment, transaction_id=transaction_id)
        obj.save()

    return GatewayResponse(
        is_success=is_success,
        action_required=False,
        transaction_id=transaction_id or "",
        amount=payment_information.amount,
        currency=payment_information.currency,
        error=authorization_response.get('error_code'),
        # payment_method_info=payment_method_info,
        kind=TransactionKind.AUTH,
        # raw_response=raw_response,
        # customer_id=customer_id,
        # searchable_key=str(searchable_key) if searchable_key else None,
    )

def capture(payment_information: PaymentData, transaction_id: str, config: GatewayConfig) -> GatewayResponse:
    backend = JSONWebTokenBackend()
    user = backend.get_user(payment_information.customer_email)
    capture_response = payment_capture(payment_information.amount, transaction_id, user.monchique_token)

    return GatewayResponse(
        is_success=capture_response['is_authorized'],
        action_required=False,
        transaction_id=capture_response.get('tx_id') or "",
        amount=payment_information.amount,
        currency=payment_information.currency,
        error=capture_response.get('error_code'),
        # payment_method_info=payment_method_info,
        kind=TransactionKind.CAPTURE,
        # raw_response=raw_response,
        # customer_id=customer_id,
        # searchable_key=str(searchable_key) if searchable_key else None,
    )

def refund(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    backend = JSONWebTokenBackend()
    user = backend.get_user(payment_information.customer_email)
    transaction_id = get_tx_id(payment_information.payment_id)
    refund_response = payment_refund(payment_information.amount, transaction_id, user.monchique_token)

    return GatewayResponse(
        is_success=refund_response['is_authorized'],
        action_required=False,
        transaction_id=refund_response.get('tx_id') or "",
        amount=payment_information.amount,
        currency=payment_information.currency,
        error=refund_response.get('error_code'),
        # payment_method_info=payment_method_info,
        kind=TransactionKind.REFUND,
        # raw_response=raw_response,
        # customer_id=customer_id,
        # searchable_key=str(searchable_key) if searchable_key else None,
    )

def void(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    # return GatewayResponse(
    #     is_success=success,
    #     action_required=False,
    #     transaction_id=transaction_id,
    #     amount=payment_information.amount,
    #     currency=payment_information.currency,
    #     error=error,
    #     payment_method_info=payment_method_info,
    #     kind=TransactionKind.VOID,
    #     raw_response=raw_response,
    #     customer_id=payment_information.customer_id,
    # )

    pass

def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Process the payment."""
    authorize_response = authorize(payment_information, config)
    if not authorize_response.is_success:
        return authorize_response

    return capture(payment_information, authorize_response.transaction_id, config)

def get_tx_id(payment_id):
    return MonchiquePayment.objects.get(payment_id=payment_id).transaction_id