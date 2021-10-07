import os
from typing import List

import opentracing

from saleor.order.models import Fulfillment

from ... import TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData
from . import api
from .api_types import ApiConfig, PaymentStatus, get_api_config


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
    with opentracing.global_tracer().start_active_span("np-atobarai.checkout.payments"):
        result = api.register_transaction(config, payment_information)

    return GatewayResponse(
        is_success=result.status == PaymentStatus.SUCCESS,
        action_required=False,
        kind=TransactionKind.AUTH,
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
    with opentracing.global_tracer().start_active_span("np-atobarai.checkout.payments"):
        result = api.cancel_transaction(config, payment_information)

    return GatewayResponse(
        is_success=result.status == PaymentStatus.SUCCESS,
        action_required=False,
        kind=TransactionKind.VOID,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=result.psp_reference,
        error=os.linesep.join(result.errors),
        raw_response=result.raw_response,
        psp_reference=result.psp_reference,
    )


@inject_api_config
def fulfillment_created(fulfillment: Fulfillment, config: ApiConfig) -> None:
    with opentracing.global_tracer().start_active_span("np-atobarai.checkout.payments"):
        # TODO: handle errors
        api.report_fulfillment(config, fulfillment)


@inject_api_config
def refund(payment_information: PaymentData, config: ApiConfig) -> GatewayResponse:
    raise NotImplementedError
