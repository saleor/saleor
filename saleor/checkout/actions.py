from decimal import Decimal
from typing import cast

from ..core.utils.events import call_event
from ..payment.models import TransactionItem
from ..plugins.manager import PluginsManager
from . import CheckoutChargeStatus
from .calculations import fetch_checkout_data
from .fetch import fetch_checkout_info, fetch_checkout_lines
from .models import Checkout
from .payment_utils import update_refundable_for_checkout


def update_last_transaction_modified_at_for_checkout(
    checkout: Checkout, transaction: TransactionItem
):
    if (
        not checkout.last_transaction_modified_at
        or checkout.last_transaction_modified_at < transaction.modified_at
    ):
        checkout.last_transaction_modified_at = transaction.modified_at
        checkout.save(update_fields=["last_transaction_modified_at"])


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

    update_last_transaction_modified_at_for_checkout(checkout, transaction)

    refundable = transaction.last_refund_success and (
        transaction.authorized_value > Decimal(0)
        or transaction.charged_value > Decimal(0)
    )
    if refundable != checkout.automatically_refundable:
        # if last_refund_status is different than automatically_refundable
        # we need to recalculate automatically_refundable based on the rest of
        # checkout's transactions
        update_refundable_for_checkout(checkout.pk)

    if not previous_charge_status_is_fully_paid and current_status_is_fully_paid:
        call_event(manager.checkout_fully_paid, checkout_info.checkout)
