from datetime import timedelta

from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils import timezone

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ... import FulfillmentStatus, OrderStatus
from ...models import Fulfillment, Order, OrderLine

# The batch of size 250 takes ~0.2 second and consumes ~20MB memory at peak
BATCH_SIZE = 250
DEFAULT_EXPIRE_TIME = 24

# The batch of size 250 takes ~0.2 second and consumes ~15MB memory at peak
ORDER_BATCH_SIZE = 250


@app.task
@allow_writer()
def set_base_price_expire_time_task():
    orders = Order.objects.filter(status="draft")
    qs = (
        OrderLine.objects.filter(Exists(orders.filter(pk=OuterRef("order_id"))))
        .filter(draft_base_price_expire_at__isnull=True)
        .order_by("pk")
    )
    line_ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    if line_ids:
        order_lines = OrderLine.objects.filter(id__in=line_ids).order_by("pk")
        now = timezone.now()
        expire_time = now + timedelta(hours=DEFAULT_EXPIRE_TIME)
        with transaction.atomic():
            _order_lines_lock = list(order_lines.select_for_update(of=(["self"])))
            order_lines.update(draft_base_price_expire_at=expire_time)

        set_base_price_expire_time_task.delay()


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
