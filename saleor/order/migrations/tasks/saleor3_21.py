from django.db import transaction
from django.db.models import Exists, OuterRef

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ... import FulfillmentStatus, OrderStatus
from ...models import Fulfillment, Order

# The batch of size 250 takes ~0.2 second and consumes ~15MB memory at peak
ORDER_BATCH_SIZE = 250


@app.task
@allow_writer()
def migrate_orders_with_waiting_for_approval_fulfillment_task():
    """Migrate order with waiting for approval fulfillment to unfulfilled status.

    If the order has a fulfillment with waiting for approval status, it will be set to unfulfilled,
    instead of `partially_fulfilled` status.
    """
    waiting_for_approval_fulfillments = Fulfillment.objects.filter(
        status=FulfillmentStatus.WAITING_FOR_APPROVAL
    )
    fulfilled_fulfillments = Fulfillment.objects.filter(
        status=FulfillmentStatus.FULFILLED
    )
    # get orders that has at least one waiting for approval fulfillment and not
    # fulfilled fulfillment
    orders = Order.objects.filter(
        Exists(waiting_for_approval_fulfillments.filter(order_id=OuterRef("id"))),
        ~Exists(fulfilled_fulfillments.filter(order_id=OuterRef("id"))),
        status=OrderStatus.PARTIALLY_FULFILLED,
    ).order_by("pk")
    ids = orders.values_list("pk", flat=True)[:ORDER_BATCH_SIZE]
    if ids:
        orders = Order.objects.filter(id__in=ids).order_by("pk")
        with transaction.atomic():
            _orders_lock = list(orders.select_for_update(of=(["self"])))
            orders.update(status=OrderStatus.UNFULFILLED)
        migrate_orders_with_waiting_for_approval_fulfillment_task.delay()
