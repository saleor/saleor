from typing import Iterable, Optional, cast

from ..discount import DiscountInfo
from ..payment.models import TransactionItem
from ..plugins.manager import PluginsManager
from .calculations import fetch_checkout_data
from .fetch import fetch_checkout_info, fetch_checkout_lines
from .models import Checkout


def transaction_amounts_for_checkout_updated(
    transaction: TransactionItem,
    discounts: Optional[Iterable["DiscountInfo"]],
    manager: "PluginsManager",
):
    if not transaction.checkout_id:
        return
    checkout = cast(Checkout, transaction.checkout)
    lines, _ = fetch_checkout_lines(checkout)
    discounts = discounts or []
    checkout_info = fetch_checkout_info(checkout, lines, discounts, manager)
    fetch_checkout_data(
        checkout_info, manager, lines, discounts=discounts, force_status_update=True
    )
    # FIXME future PR will add a webhook for fully-paid checkouts.
