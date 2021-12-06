from django.utils import timezone

from ....order.models import Order


def invalidate_order_prices(order: Order) -> None:
    order.price_expiration_for_unconfirmed = timezone.now()
    order.save(update_fields=["price_expiration_for_unconfirmed"])
