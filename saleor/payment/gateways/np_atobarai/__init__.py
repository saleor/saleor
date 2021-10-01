from ...interface import GatewayConfig, GatewayResponse, PaymentData


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    raise NotImplementedError


def capture(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    raise NotImplementedError


def void(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    raise NotImplementedError


def refund(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    raise NotImplementedError
