from django.utils import timezone

from ....order import ORDER_EDITABLE_STATUS
from ....order.models import Order


def invalidate_order_prices(order: Order, *, save: bool) -> None:
    """Mark order as ready for prices recalculation.

    Does nothing if order is not editable
    (it's status is neither draft, nor unconfirmed).
    """
    if order.status not in ORDER_EDITABLE_STATUS:
        return

    order.price_expiration_for_unconfirmed = timezone.now()

    if save:
        order.save(update_fields=["price_expiration_for_unconfirmed"])
