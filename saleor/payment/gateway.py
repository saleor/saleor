from ..core.payments import PaymentInterface, Gateway
from ..extensions.manager import get_extensions_manager
from .models import Payment, Transaction
from .utils import create_payment_information, create_transaction


class PaymentGateway:
    def __init__(self):
        self.plugin_manager: PaymentInterface = get_extensions_manager()

    def process_payment(
        self, gateway: Gateway, payment: Payment, token: str
    ) -> Transaction:
        payment_data = create_payment_information(payment=payment, payment_token=token)
        response = self.plugin_manager.process_payment(gateway, payment_data, token)
        return create_transaction(
            payment,
            kind=response.kind,
            payment_information=payment_data,
            gateway_response=response,
        )
