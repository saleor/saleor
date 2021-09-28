import opentracing

from saleor.payment import TransactionKind
from saleor.payment.gateways.np_atobarai import api
from saleor.payment.gateways.np_atobarai.api_types import (
    ApiConfig,
    PaymentStatus,
    get_api_config,
)

from ...interface import GatewayConfig, GatewayResponse, PaymentData


def inject_api_config(fun):
    def inner(payment_information: PaymentData, config: GatewayConfig):
        return fun(payment_information, get_api_config(config.connection_params))

    return inner


@inject_api_config
def process_payment(
    payment_information: PaymentData, config: ApiConfig
) -> GatewayResponse:
    with opentracing.global_tracer().start_active_span("np-atobarai.checkout.payments"):
        result = api.register_transaction(config, payment_information)

    return GatewayResponse(
        is_success=result.status == PaymentStatus.SUCCESS,
        action_required=result.status != PaymentStatus.PENDING,
        kind=TransactionKind.AUTH,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=result.psp_reference,
        error="",
        psp_reference=result.psp_reference,
    )


@inject_api_config
def capture(payment_information: PaymentData, config: ApiConfig) -> GatewayResponse:
    raise NotImplementedError


@inject_api_config
def void(payment_information: PaymentData, config: ApiConfig) -> GatewayResponse:
    raise NotImplementedError


@inject_api_config
def refund(payment_information: PaymentData, config: ApiConfig) -> GatewayResponse:
    raise NotImplementedError
