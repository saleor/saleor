from collections.abc import Iterable

from ..celeryconf import app
from ..checkout.models import CheckoutDelivery
from ..core.db.connection import allow_writer
from ..order import ORDER_EDITABLE_STATUS
from ..order.models import Order


@app.task
@allow_writer()
def drop_invalid_shipping_methods_relations_for_given_channels(
    shipping_method_ids: Iterable[str | int],
    channel_ids: Iterable[str | int],
):
    # Mark existing deliveries as invalid
    CheckoutDelivery.objects.filter(
        built_in_shipping_method_id__in=shipping_method_ids
    ).update(is_valid=False)

    # unlink shipping methods from order instances
    # when method is no longer available in given channels
    Order.objects.filter(
        status__in=ORDER_EDITABLE_STATUS,
        shipping_method_id__in=shipping_method_ids,
        channel_id__in=channel_ids,
    ).update(shipping_method=None, should_refresh_prices=True)
