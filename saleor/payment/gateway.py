from ..core.payments import PaymentInterface, Gateway
from ..extensions.manager import get_extensions_manager
from .models import Payment, Transaction
from .utils import create_payment_information


class PaymentGateway:
    def __init__(self):
        self.plugin_manager: PaymentInterface = get_extensions_manager()

    def process_payment(
        self, gateway: Gateway, payment: Payment, token: str
    ) -> Transaction:
        payment_data = create_payment_information(payment=payment, payment_token=token)
        self.plugin_manager.process_payment(gateway, payment_data, token)
