import logging
from decimal import Decimal
from typing import List

from celery.exceptions import SoftTimeLimitExceeded
from django.utils import timezone

from ..celeryconf import app
from ..core.tasks import celery_task_lock
from ..core.tracing import traced_atomic_transaction
from ..plugins.manager import get_plugins_manager
from . import OrderStatus
from .actions import expire_order
from .models import Order
from .utils import invalidate_order_prices

logger = logging.getLogger(__name__)


@app.task
def recalculate_orders_task(order_ids: List[int]):
    orders = Order.objects.filter(id__in=order_ids)

    for order in orders:
        invalidate_order_prices(order)

    Order.objects.bulk_update(orders, ["should_refresh_prices"])


@app.task
def send_order_updated(order_ids):
    manager = get_plugins_manager()
    for order in Order.objects.filter(id__in=order_ids):
        manager.order_updated(order)


def _batch_ids(iterable, batch_size=1):
    length = len(iterable)
    for index in range(0, length, batch_size):
        yield iterable[index : min(index + batch_size, length)]


def _queryset_in_batches(queryset):
    ids = queryset.values_list("id", flat=True)
    for ids_batch in _batch_ids(ids, 1000):
        yield ids_batch


def _expire_orders(manager, now):
    qs = Order.objects.filter(
        status=OrderStatus.UNCONFIRMED,
        channel__expire_orders_after__isnull=False,
        total_charged_amount=Decimal(0),
    ).select_related("channel")
    for ids_batch in _queryset_in_batches(qs):
        with traced_atomic_transaction():
            orders = Order.objects.filter(id__in=ids_batch).prefetch_related("user")
            orders_to_update = []
            for order in orders:
                if _process_order(order, manager, now):
                    orders_to_update.append(order)
            Order.objects.bulk_update(orders_to_update, ["status", "updated_at"])


def _process_order(order, manager, now):
    if (
        order.channel.expire_orders_after is not None
        and order.created_at
        <= now - timezone.timedelta(minutes=order.channel.expire_orders_after)
    ):
        expire_order(order, order.user, manager, save_order_object=False)
        return True
    return False


@app.task(soft_time_limit=60 * 30)
def expire_orders_task():
    now = timezone.now()
    task_name = "expire_orders"
    manager = get_plugins_manager()
    try:
        with celery_task_lock(task_name) as (lock_obj, acquired):
            if lock_obj.created_at < now - timezone.timedelta(hours=1):
                logger.error("%s task exceeded 1h working time.", [task_name])
            if acquired:
                _expire_orders(manager, now)

    except SoftTimeLimitExceeded as e:
        logger.error(e)
