from collections.abc import Iterable

from django.utils import timezone

from ..celeryconf import app
from ..checkout.models import Checkout
from ..core.db.connection import allow_writer
from ..order import ORDER_EDITABLE_STATUS
from ..order.models import Order


@app.task
@allow_writer()
def drop_invalid_shipping_methods_relations_for_given_channels(
    shipping_method_ids: Iterable[str | int],
    channel_ids: Iterable[str | int],
):
    # unlink shipping methods from order and checkout instances
    # when method is no longer available in given channels
    current_time = timezone.now()
    Checkout.objects.filter(
        shipping_method_id__in=shipping_method_ids, channel_id__in=channel_ids
    ).update(
        shipping_method=None,
        price_expiration=current_time,
        discount_expiration=current_time,
        last_change=current_time,
    )
    Order.objects.filter(
        status__in=ORDER_EDITABLE_STATUS,
        shipping_method_id__in=shipping_method_ids,
        channel_id__in=channel_ids,
    ).update(shipping_method=None, should_refresh_prices=True)
