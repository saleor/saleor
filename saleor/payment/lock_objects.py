from typing import TYPE_CHECKING, Optional
from uuid import UUID

from django.db.models import QuerySet

from ..checkout.lock_objects import checkout_qs_select_for_update
from ..order.lock_objects import order_qs_select_for_update
from .models import TransactionItem

if TYPE_CHECKING:
    from ..checkout.models import Checkout
    from ..order.models import Order


def transaction_item_qs_select_for_update() -> QuerySet[TransactionItem]:
    return TransactionItem.objects.order_by("pk").select_for_update(of=["self"])


def get_order_and_transaction_item_locked_for_update(
    order_id: UUID, transaction_item_id: int
) -> tuple["Order", TransactionItem]:
    order = order_qs_select_for_update().get(pk=order_id)
    transaction_item = transaction_item_qs_select_for_update().get(
        pk=transaction_item_id
    )
    return order, transaction_item


def get_checkout_and_transaction_item_locked_for_update(
    checkout_id: UUID, transaction_item_id: int
) -> tuple[Optional["Checkout"], TransactionItem]:
    checkout = checkout_qs_select_for_update().filter(pk=checkout_id).first()
    transaction_item = transaction_item_qs_select_for_update().get(
        pk=transaction_item_id
    )
    return checkout, transaction_item
