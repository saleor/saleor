from operator import attrgetter
from typing import List

from prices import Money

from ..core.taxes import zero_money
from . import ChargeStatus
from .models import Payment


def get_last_payment(payments: List[Payment]):
    return max(payments, default=None, key=attrgetter("pk"))


def get_total_captured(payments: List[Payment], fallback_currency: str):
    # FIXME adjust to multiple payments in the future
    if last_payment := get_last_payment(payments):
        if last_payment.charge_status in (  # type: ignore
            ChargeStatus.PARTIALLY_CHARGED,
            ChargeStatus.FULLY_CHARGED,
            ChargeStatus.PARTIALLY_REFUNDED,
        ):
            return Money(
                last_payment.captured_amount, last_payment.currency  # type: ignore
            )
    return zero_money(fallback_currency)
