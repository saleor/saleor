from datetime import timedelta
from decimal import Decimal

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

# The batch of size 250 takes ~0.3 second and consumes ~12MB memory at peak
LINES_COUNT_BATCH_SIZE = 250


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


@app.task
@allow_writer()
def set_lines_count_task(order_number=0):
    """Set lines count for orders."""
    orders = Order.objects.filter(number__gte=order_number, lines_count__isnull=True)
    qs = orders.order_by("number")
    numbers = list(qs.values_list("number", flat=True)[:LINES_COUNT_BATCH_SIZE])
    if numbers:
        orders = Order.objects.filter(number__in=numbers).order_by("pk")
        with transaction.atomic():
            to_save = []
            _orders_lock = list(orders.select_for_update(of=(["self"])))
            for order in orders:
                order.lines_count = order.lines.count()
                to_save.append(order)
            Order.objects.bulk_update(to_save, ["lines_count"])
        set_lines_count_task.delay(numbers[-1])


@app.task
@allow_writer()
def fix_negative_total_net_for_orders_using_gift_cards_task(start_pk=0):
    # No memory usage tests were conducted here.
    # It's assumed that loading 500 identifiers to memory is not straining the memory
    # usage.
    BATCH_SIZE = 500

    with transaction.atomic():
        # Following select query has been tested on database with 4.2m actual orders, it took ~5s.
        order_pks = list(
            Order.objects.filter(
                pk__gt=start_pk,
                total_net_amount__lt=Decimal("0.00"),
            )
            .exclude(gift_cards=None)
            .order_by("pk")
            .select_for_update()
            .values_list("pk", flat=True)[:BATCH_SIZE]
        )

        if not order_pks:
            return

        Order.objects.filter(
            pk__in=order_pks,
        ).update(total_net_amount=Decimal("0.00"))

        fix_negative_total_net_for_orders_using_gift_cards_task.delay(
            start_pk=order_pks[-1]
        )
