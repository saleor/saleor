from typing import Iterable, Union

from ..celeryconf import app
from ..checkout.models import Checkout
from ..graphql.order.mutations.utils import ORDER_EDITABLE_STATUS
from ..order.models import Order


@app.task
def drop_invalid_shipping_methods_relations_for_given_channels(
    shipping_method_ids: Iterable[Union[str, int]],
    channel_ids: Iterable[Union[str, int]],
):
    # unlink shipping methods from order and checkout instances
    # when method is no longer available in given channels
    Checkout.objects.filter(
        shipping_method_id__in=shipping_method_ids, channel_id__in=channel_ids
    ).update(shipping_method=None)
    Order.objects.filter(
        status__in=ORDER_EDITABLE_STATUS,
        shipping_method_id__in=shipping_method_ids,
        channel_id__in=channel_ids,
    ).update(shipping_method=None)
