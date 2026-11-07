from collections.abc import Iterable
from operator import attrgetter
from typing import TYPE_CHECKING

from ..core.taxes import zero_money, zero_taxed_money
from . import ChargeStatus
from .models import Payment

if TYPE_CHECKING:
    from ..order.models import OrderLine


def get_last_payment(payments: Iterable[Payment]):
    return max(payments, default=None, key=attrgetter("pk"))


def legacy_payment_holds_refunds(payment: Payment | None) -> bool:
    """Return True when a legacy payment is the source of the refunded amount.

    A legacy payment keeps the refunds in its refund transactions while it is active,
    and reports them through its charge status once it is fully refunded.
    """
    if payment is None:
        return False
    return bool(
        payment.is_active or payment.charge_status == ChargeStatus.FULLY_REFUNDED
    )


def get_total_authorized(payments: Iterable[Payment], fallback_currency: str):
    # FIXME adjust to multiple payments in the future
    if last_payment := get_last_payment(payments):
        if last_payment.is_active:
            return last_payment.get_authorized_amount()
    return zero_money(fallback_currency)


def get_subtotal(order_lines: Iterable["OrderLine"], fallback_currency: str):
    subtotal_iterator = (line.total_price for line in order_lines)
    return sum(subtotal_iterator, zero_taxed_money(currency=fallback_currency))
