import logging
import os
from typing import List

from saleor.order.models import Fulfillment

from ... import TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData
from ...models import Payment
from . import api
from .api_types import ApiConfig, PaymentResult, PaymentStatus, get_api_config

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
    errors = api.report_fulfillment(config, fulfillment)

    if errors:
        logger.error("Could not capture payment in NP Atobarai: %s" ", ".join(errors))


@inject_api_config
def refund(payment_information: PaymentData, config: ApiConfig) -> GatewayResponse:
    payment = Payment.objects.get(pk=payment_information.payment_id)

    if payment_information.amount < payment.captured_amount:
        # TODO: is it even possible to have a payment here without psp reference?
        assert payment.psp_reference
        # TODO: does it make sense?
        result = PaymentResult(
            status=PaymentStatus.FAILED,
            psp_reference=payment.psp_reference,
            errors=["Cannot partially refund transaction in NP."],
        )
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
