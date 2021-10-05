from dataclasses import dataclass
from decimal import Decimal

from saleor.payment.models import Payment


@dataclass
class OrderPaymentAction:
    """Used to transmit data about payment-related events."""

    payment: Payment
    amount: Decimal
    include_shipping_costs: bool = False
    from_deprecated_request: bool = False
