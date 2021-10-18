import logging
import os
from typing import List

from ....order.models import Fulfillment
from ... import PaymentError, TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData
from ...models import Payment
from . import api
from .api_types import ApiConfig, PaymentStatus, get_api_config
from .utils import (
    fulfillment_is_captured,
    mark_fulfillment_as_captured,
    notify_dashboard,
)

logger = logging.getLogger(__name__)


def inject_api_config(fun):
    def inner(payment_information: PaymentData, config: GatewayConfig):
        return fun(payment_information, get_api_config(config.connection_params))

    return inner


def parse_errors(errors: List[str]) -> str:
    # FIXME: better solution?
    #  Transaction.error in database has max_length of 256
    return os.linesep.join(errors)[:256]


@inject_api_config
def process_payment(
    payment_information: PaymentData, config: ApiConfig
) -> GatewayResponse:
    result = api.register_transaction(config, payment_information)

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


@inject_api_config
def capture(payment_information: PaymentData, config: ApiConfig) -> GatewayResponse:
    raise NotImplementedError


@inject_api_config
def void(payment_information: PaymentData, config: ApiConfig) -> GatewayResponse:
    raise NotImplementedError


@inject_api_config
def tracking_number_updated(fulfillment: Fulfillment, config: ApiConfig) -> None:
    order = fulfillment.order

    if not fulfillment.lines.count() == order.lines.count():
        errors = ["Cannot report tracking lines for partial fulfillments."]
    else:
        errors = api.report_fulfillment(config, fulfillment)

    if errors:
        error = ", ".join(errors)
        logger.warning("Could not capture payment in NP Atobarai: %s", error)
        notify_dashboard(order, "Capture Error: Partial Fulfillment")
    else:
        mark_fulfillment_as_captured(fulfillment)


@inject_api_config
def refund(payment_information: PaymentData, config: ApiConfig) -> GatewayResponse:
    payment_id = payment_information.payment_id
    payment = Payment.objects.filter(pk=payment_id).first()

    if not payment:
        raise PaymentError(f"Payment with id {payment_id} does not exist.")

    if payment_information.amount < payment.captured_amount:
        order = payment.order
        if not order:
            raise PaymentError(f"Order does not exist for payment with id {payment_id}")

        fulfillment = order.fulfillments.order_by("fulfillment_order").first()
        lines = payment_information.lines_to_refund

        if fulfillment_is_captured(fulfillment):
            result = api.transaction_reregistration_for_partial_return(
                config, payment, payment_information, lines
            )
        else:
            result = api.change_transaction(config, payment, payment_information, lines)
    else:
        result = api.cancel_transaction(config, payment_information)

    return GatewayResponse(
        is_success=result.status == PaymentStatus.SUCCESS,
        action_required=False,
        kind=TransactionKind.REFUND,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=result.psp_reference,
        error=os.linesep.join(result.errors),
        raw_response=result.raw_response,
        psp_reference=result.psp_reference,
    )
