from typing import cast

from ..core.utils.events import call_event
from ..payment.models import TransactionItem
from ..plugins.manager import PluginsManager
from . import CheckoutChargeStatus
from .calculations import fetch_checkout_data
from .fetch import fetch_checkout_info, fetch_checkout_lines
from .models import Checkout


def transaction_amounts_for_checkout_updated(
    transaction: TransactionItem,
    manager: "PluginsManager",
):
    if not transaction.checkout_id:
        return
    checkout = cast(Checkout, transaction.checkout)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    previous_charge_status = checkout_info.checkout.charge_status
    fetch_checkout_data(checkout_info, manager, lines, force_status_update=True)
    previous_charge_status_is_fully_paid = previous_charge_status in [
        CheckoutChargeStatus.FULL,
        CheckoutChargeStatus.OVERCHARGED,
    ]
    current_status_is_fully_paid = checkout_info.checkout.charge_status in [
        CheckoutChargeStatus.FULL,
        CheckoutChargeStatus.OVERCHARGED,
    ]
    if not previous_charge_status_is_fully_paid and current_status_is_fully_paid:
        call_event(manager.checkout_fully_paid, checkout_info.checkout)
