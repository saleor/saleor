from typing import Dict

from ... import TransactionKind

from ...interface import GatewayConfig, GatewayResponse, PaymentData

from .forms import PayrexxPaymentForm
from .utils import get_payrexx_link


def get_client_token(config: GatewayConfig) -> str:
    return


def authorize(payment_information: PaymentData,
              config: GatewayConfig) -> GatewayConfig:
    return capture(payment_information, config)


def capture(payment_information: PaymentData,
            config: GatewayConfig) -> GatewayConfig:
    payrexx_hash, _, payrexx_id = payment_information.token.rpartition(':')

    payrexx_link = get_payrexx_link(payrexx_id, config.connection_params)
    error = None

    response = dict()
    if not payrexx_hash == payrexx_link['hash']:
        return _create_response(
            payment_information,
            kind=TransactionKind.VOID,
            response=response,
            error='processing_error',
            token=payrexx_hash
            )

    if payrexx_link['status'] == 'confirmed':
        kind = TransactionKind.CAPTURE
    elif payrexx_link['status'] == 'auth':
        kind = TransactionKind.AUTH
    else:
        kind = TransactionKind.VOID

    return _create_response(
        payment_information,
        kind=kind,
        response=response,
        error=error,
        token=payrexx_hash
        )


def refund(payment_information: PaymentData,
           config: GatewayConfig) -> GatewayConfig:
    pass


def void(payment_information: PaymentData,
         config: GatewayConfig) -> GatewayConfig:
    pass


def process_payment(payment_information: PaymentData,
                    config: GatewayConfig) -> GatewayConfig:
    # TODO: Capture stuff
    return capture(payment_information, config)


def create_form(data: Dict,
                payment_information: PaymentData,
                connection_params: Dict) -> PayrexxPaymentForm:
    return PayrexxPaymentForm(
        data=data,
        payment_information=payment_information,
        gateway_params=connection_params,
        )


def _create_response(payment_information: PaymentData,
                     kind: str, response: Dict, error: str, token: str
                     ) -> GatewayResponse:
    pass

    return GatewayResponse(
        True,
        kind,
        payment_information.amount,
        payment_information.currency,
        token,
        error
        )
