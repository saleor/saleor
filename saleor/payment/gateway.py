import logging

from django.core.exceptions import ImproperlyConfigured

from ..core.payments import Gateway, PaymentInterface
from ..extensions.manager import get_extensions_manager

from . import GatewayError, TransactionKind
from .models import Payment, Transaction
from .utils import (
    create_payment_information,
    create_transaction,
    validate_gateway_response,
    _gateway_postprocess,
)

logger = logging.getLogger(__name__)


class PaymentGateway:
    def __init__(self):
        self.plugin_manager: PaymentInterface = get_extensions_manager()

    def process_payment(
        self, payment: Payment, token: str, store_source: bool = False
    ) -> Transaction:
        payment_data = create_payment_information(
            payment=payment, payment_token=token, store_source=store_source
        )
        gateway = _get_gateway(payment)
        txn, response = None, None
        try:
            response = self.plugin_manager.process_payment(gateway, payment_data)
            validate_gateway_response(response)
        except GatewayError:
            error_msg = "Gateway response validation failed"
            logger.exception(error_msg)
            response = None  # Set response empty as the validation failed
        except Exception:
            error_msg = "Gateway encountered an error"
            logger.exception(error_msg)
        finally:
            txn = create_transaction(
                payment,
                kind=TransactionKind.CAPTURE,
                payment_information=payment_data,
                gateway_response=response,
            )
        _gateway_postprocess(txn, payment)
        return txn


def _get_gateway(payment: Payment) -> Gateway:
    try:
        gateway = Gateway(payment.gateway)
    except AttributeError:
        raise ImproperlyConfigured("Payment gateway %s is not configured." % gateway)

    return gateway
