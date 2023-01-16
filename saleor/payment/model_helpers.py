from operator import attrgetter
from typing import TYPE_CHECKING, Iterable

from ..core.taxes import zero_money, zero_taxed_money
from .models import Payment

if TYPE_CHECKING:
    from ..order.models import OrderLine


def get_last_payment(payments: Iterable[Payment]):
    # Skipping a partial payment is a temporary workaround for storing a basic data
    # about partial payment from Adyen plugin. This is something that will removed in
    # 3.1 by introducing a partial payments feature
    valid_payments = [payment for payment in payments if not payment.partial]
    return max(valid_payments, default=None, key=attrgetter("pk"))


def get_total_authorized(payments: Iterable[Payment], fallback_currency: str):
    # FIXME adjust to multiple payments in the future
    if last_payment := get_last_payment(payments):
        if last_payment.is_active:
            return last_payment.get_authorized_amount()
    return zero_money(fallback_currency)


def get_subtotal(order_lines: Iterable["OrderLine"], fallback_currency: str):
    subtotal_iterator = (line.total_price for line in order_lines)
    return sum(subtotal_iterator, zero_taxed_money(currency=fallback_currency))
