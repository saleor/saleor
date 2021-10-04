import os

import opentracing

from ... import TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData
from . import api
from .api_types import PaymentStatus, get_api_config


def inject_api_config(fun):
    def inner(payment_information: PaymentData, config: GatewayConfig):
        return fun(payment_information, get_api_config(config.connection_params))

    return inner


@inject_api_config
def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    raise NotImplementedError


@inject_api_config
def capture(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    raise NotImplementedError


@inject_api_config
def void(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    with opentracing.global_tracer().start_active_span("np-atobarai.checkout.payments"):
        result = api.cancel_transaction(config, payment_information)  # type: ignore

    return GatewayResponse(
        is_success=result.status == PaymentStatus.SUCCESS,
        action_required=False,
        kind=TransactionKind.VOID,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=result.psp_reference,
        error=os.linesep.join(result.errors),
        psp_reference=result.psp_reference,
    )


@inject_api_config
def refund(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    raise NotImplementedError
