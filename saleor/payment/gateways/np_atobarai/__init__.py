import logging
import os

from graphene import Node

from ....order.models import Fulfillment
from ... import PaymentError, TransactionKind
from ...interface import GatewayResponse, PaymentData
from ...models import Payment
from . import api
from .api_helpers import get_goods_with_refunds
from .api_types import ApiConfig, PaymentStatus
from .const import NP_PLUGIN_ID
from .utils import (
    get_fulfillment_for_order,
    get_shipping_company_code,
    notify_dashboard,
)

logger = logging.getLogger(__name__)


def parse_errors(errors: list[str]) -> str:
    # Field error of Transaction db model has max length of 256
    # Error codes have max length of 11
    # We are limiting errors to maximum of 11 codes, because:
    # 11 * 11 + 10 * 2 (max length of linesep) == 141 < 256
    return os.linesep.join(errors[:11])


def process_payment(
    payment_information: PaymentData, config: ApiConfig
) -> GatewayResponse:
    """Create new transaction in NP Atobarai.

    Returns unsuccessful response if payment status from
    NP response is PENDING or FAILED.
    """
    result = api.register_transaction(config, payment_information)

    return GatewayResponse(
        is_success=result.status == PaymentStatus.SUCCESS,
        action_required=False,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=result.psp_reference or "",
        error=parse_errors(result.errors),
        raw_response=result.raw_response,
        psp_reference=result.psp_reference,
    )


def capture(payment_information: PaymentData, config: ApiConfig) -> GatewayResponse:
    raise NotImplementedError


def void(payment_information: PaymentData, config: ApiConfig) -> GatewayResponse:
    raise NotImplementedError


def tracking_number_updated(fulfillment: Fulfillment, config: ApiConfig) -> None:
    """Event callback on updating order tracking number.

    Captures payment in NP Atobarai and sends dashboard notification of the result.
    """
    order = fulfillment.order
    payments = order.payments.filter(gateway=NP_PLUGIN_ID, is_active=True)

    if not payments:
        logger.warning("No active payments for this order")
        notify_dashboard(order, "No active payments for this order")
        return

    results = [
        (payment.id, *api.report_fulfillment(config, payment, fulfillment))
        for payment in payments
    ]

    for payment_id, errors, already_captured in results:
        payment_graphql_id = Node.to_global_id("Payment", payment_id)

        if already_captured:
            logger.warning(
                "Payment with id %s was already captured", payment_graphql_id
            )
            msg = f"Error: Payment with id {payment_graphql_id} was already captured"
        elif errors:
            error = ", ".join(errors)
            logger.warning(
                f"Could not capture payment with id {payment_graphql_id} "
                f"in NP Atobarai: {error}"
            )
            msg = (
                f"Error: Cannot capture payment with id {payment_graphql_id} ({error})"
            )
        else:
            msg = f"Payment with id {payment_graphql_id} was captured"

        notify_dashboard(order, msg)


def refund(payment_information: PaymentData, config: ApiConfig) -> GatewayResponse:
    """Refund an existing transaction.

    A new psp reference may be issued,
    which will be saved in payment object.
    """
    payment_id = payment_information.payment_id
    payment = Payment.objects.filter(pk=payment_id).first()

    if not payment:
        raise PaymentError(f"Payment with id {payment_id} does not exist.")

    goods, billed_amount = get_goods_with_refunds(config, payment, payment_information)

    # in case of refunding less than already captured
    # and not all lines are being refunded,
    # the transaction needs to be re-registered in NP Atobarai
    if payment_information.amount < payment.captured_amount:
        order = payment.order

        if not order:
            raise PaymentError(
                f"Order does not exist for payment with id {payment_id}."
            )

        result = api.change_transaction(
            config,
            payment,
            payment_information,
            goods,
            billed_amount,
        )

        if result.status == PaymentStatus.FOR_REREGISTRATION:
            fulfillment = get_fulfillment_for_order(order)
            shipping_company_code = get_shipping_company_code(config, fulfillment)
            tracking_number = fulfillment.tracking_number
            result = api.reregister_transaction_for_partial_return(
                config,
                payment,
                payment_information,
                shipping_company_code,
                tracking_number,
                goods,
                billed_amount,
            )

    else:
        result = api.cancel_transaction(config, payment_information)

    new_psp_reference = result.psp_reference
    if new_psp_reference and payment.psp_reference != new_psp_reference:
        payment.psp_reference = new_psp_reference
        payment.save(update_fields=["psp_reference"])

    return GatewayResponse(
        is_success=result.status == PaymentStatus.SUCCESS,
        action_required=False,
        kind=TransactionKind.REFUND,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=result.psp_reference or "",
        error=parse_errors(result.errors),
        raw_response=result.raw_response,
        psp_reference=result.psp_reference,
    )
