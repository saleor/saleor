import logging
import os
from typing import List

from ....order.models import Fulfillment
from ... import PaymentError, TransactionKind
from ...interface import GatewayResponse, PaymentData
from ...models import Payment
from . import api
from .api_types import ApiConfig, PaymentStatus
from .const import NP_PLUGIN_ID
from .utils import (
    get_fulfillment_for_order,
    get_payment_name,
    get_shipping_company_code,
    notify_dashboard,
)

logger = logging.getLogger(__name__)


def parse_errors(errors: List[str]) -> str:
    # Field error of Transaction db model has max length of 256
    # Error codes have max length of 11
    # We are limiting errors to maximum of 11 codes, because:
    # 11 * 11 + 10 * 2 (max length of linesep) == 141 < 256
    return os.linesep.join(errors[:11])


def process_payment(
    payment_information: PaymentData, config: ApiConfig
) -> GatewayResponse:
    payment_id = payment_information.payment_id
    payment = Payment.objects.filter(pk=payment_id).first()

    if not payment:
        logger.error(
            "Payment with id %s does not exist",
            payment_information.graphql_payment_id,
        )
        raise PaymentError("Payment does not exist.")

    result = api.register_transaction(payment.order, config, payment_information)

    return GatewayResponse(
        is_success=result.status == PaymentStatus.SUCCESS,
        action_required=False,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=result.psp_reference,
        error=parse_errors(result.errors),
        raw_response=result.raw_response,
        psp_reference=result.psp_reference,
    )


def capture(payment_information: PaymentData, config: ApiConfig) -> GatewayResponse:
    raise NotImplementedError


def void(payment_information: PaymentData, config: ApiConfig) -> GatewayResponse:
    raise NotImplementedError


def tracking_number_updated(fulfillment: Fulfillment, config: ApiConfig) -> None:
    order = fulfillment.order
    payments = order.payments.filter(gateway=NP_PLUGIN_ID, is_active=True)

    if payments:
        results = [
            api.report_fulfillment(config, payment, fulfillment) for payment in payments
        ]
    else:
        results = [("", ["No active payments for this order"], False)]

    for payment_id, errors, already_captured in results:
        payment_name = get_payment_name(payment_id)

        if already_captured:
            logger.warning("%s was already captured", payment_name.capitalize())
            notify_dashboard(
                order, f"Error: {payment_name.capitalize()} was already captured"
            )
        elif errors:
            error = ", ".join(errors)
            logger.warning(f"Could not capture {payment_name} in NP Atobarai: {error}")
            notify_dashboard(order, f"Capture Error for {payment_name}")
        else:
            notify_dashboard(order, f"Captured {payment_name}")


def refund(payment_information: PaymentData, config: ApiConfig) -> GatewayResponse:
    payment_id = payment_information.payment_id
    payment = Payment.objects.filter(pk=payment_id).first()

    if not payment:
        raise PaymentError(f"Payment with id {payment_id} does not exist.")

    if payment_information.amount < payment.captured_amount:
        order = payment.order

        if not order:
            raise PaymentError(
                f"Order does not exist for payment with id {payment_id}."
            )

        refund_data = payment_information.refund_data

        result = api.change_transaction(
            config, payment, payment_information, refund_data
        )

        if not result:
            fulfillment = get_fulfillment_for_order(order)
            shipping_company_code = get_shipping_company_code(config, fulfillment)
            tracking_number = fulfillment.tracking_number
            result = api.reregister_transaction_for_partial_return(
                config,
                payment,
                payment_information,
                shipping_company_code,
                tracking_number,
                refund_data,
            )

    else:
        result = api.cancel_transaction(config, payment_information)

    # NP may issue a new psp reference on partial refunds
    if psp_reference := result.psp_reference:
        payment.psp_reference = psp_reference
        payment.save(update_fields=["psp_reference"])

    return GatewayResponse(
        is_success=result.status == PaymentStatus.SUCCESS,
        action_required=False,
        kind=TransactionKind.REFUND,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=result.psp_reference,
        error=parse_errors(result.errors),
        raw_response=result.raw_response,
        psp_reference=result.psp_reference,
    )
