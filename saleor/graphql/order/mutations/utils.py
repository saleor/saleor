from typing import List

from django.utils import timezone

from ....order import OrderStatus
from ....order.models import Order


def invalidate_order_prices(order: Order, *, save: bool) -> List[str]:
    if order.status not in {OrderStatus.DRAFT, OrderStatus.UNCONFIRMED}:
        return []

    order.price_expiration_for_unconfirmed = timezone.now()
    updated_fields = ["price_expiration_for_unconfirmed"]
    if not save:
        return updated_fields

    order.save(update_fields=updated_fields)
    return []
