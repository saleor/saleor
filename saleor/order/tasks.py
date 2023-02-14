import logging
from decimal import Decimal
from typing import List

from celery.exceptions import SoftTimeLimitExceeded
from django.db.models import Exists, F, OuterRef
from django.db.models.functions import Extract
from django.utils import timezone

from ..celeryconf import app
from ..core.tasks import celery_task_lock
from ..core.tracing import traced_atomic_transaction
from ..core.utils.events import call_event
from ..discount.models import Voucher, VoucherCustomer
from ..payment.models import Payment, TransactionItem
from ..plugins.manager import get_plugins_manager
from ..warehouse.management import deallocate_stock_for_orders
from . import OrderStatus
from .models import Order
from .utils import invalidate_order_prices

logger = logging.getLogger(__name__)

ORDER_BATCH_SIZE = 1000


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
    for ids_batch in _batch_ids(ids, ORDER_BATCH_SIZE):
        yield ids_batch


def _bulk_release_voucher_usage(order_ids):
    voucher_orders = Order.objects.filter(
        voucher=OuterRef("pk"),
        id__in=order_ids,
    )
    Voucher.objects.filter(
        Exists(voucher_orders),
        usage_limit__isnull=False,
    ).update(used=F("used") - 1)

    voucher_customer_orders = Order.objects.filter(
        voucher=OuterRef("voucher__id"),
        user_email=OuterRef("customer_email"),
        id__in=order_ids,
    )
    VoucherCustomer.objects.filter(Exists(voucher_customer_orders)).delete()


def _call_expired_order_events(order_ids, manager):
    orders = Order.objects.filter(id__in=order_ids)
    for order in orders:
        call_event(manager.order_expired, order)
        call_event(manager.order_updated, order)


def _expire_orders(manager, now):
    qs = Order.objects.filter(
        ~Exists(TransactionItem.objects.filter(order=OuterRef("pk"))),
        ~Exists(Payment.objects.filter(order=OuterRef("pk"))),
        status=OrderStatus.UNCONFIRMED,
        channel__expire_orders_after__isnull=False,
        channel__expire_orders_after__lte=Extract(now - F("created_at"), "epoch"),
        total_charged_amount=Decimal(0),
    )
    for ids_batch in _queryset_in_batches(qs):
        with traced_atomic_transaction():
            Order.objects.filter(id__in=ids_batch).update(status=OrderStatus.EXPIRED)

            _bulk_release_voucher_usage(ids_batch)
            deallocate_stock_for_orders(ids_batch, manager)
            _call_expired_order_events(ids_batch, manager)


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
