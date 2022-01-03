from typing import List

from django.utils import timezone

from ....order import ORDER_EDITABLE_STATUS
from ....order.models import Order


def invalidate_order_prices(order: Order, *, save: bool) -> List[str]:
    """Mark order as ready for prices recalculation.

    Does nothing if order is not editable
    (it's status is neither draft, nor unconfirmed).
    """
    if order.status not in ORDER_EDITABLE_STATUS:
        return []

    order.price_expiration_for_unconfirmed = timezone.now()
    updated_fields = ["price_expiration_for_unconfirmed"]
    if not save:
        return updated_fields

    order.save(update_fields=updated_fields)
    return []
