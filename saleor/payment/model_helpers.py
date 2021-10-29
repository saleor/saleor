from typing import TYPE_CHECKING, List

from ..core.taxes import zero_money, zero_taxed_money
from .models import Payment

if TYPE_CHECKING:
    from ..order.models import OrderLine


def get_total_authorized(payments: List[Payment], fallback_currency: str):
    authorized_payments = [p for p in payments if p.is_authorized and p.is_active]
    total = zero_money(fallback_currency)
    for payment in authorized_payments:
        total.amount += payment.total
    return total


def get_subtotal(order_lines: List["OrderLine"], fallback_currency: str):
    subtotal_iterator = (line.total_price for line in order_lines)
    return sum(subtotal_iterator, zero_taxed_money(currency=fallback_currency))
