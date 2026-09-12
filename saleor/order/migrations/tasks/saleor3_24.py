from decimal import Decimal

from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ...lock_objects import order_qs_select_for_update
from ...models import Order
from ...utils import (
    _get_total_charged,
    _get_total_charged_before_refunds,
    _get_total_refund_pending,
    _get_total_refunded,
    update_order_charge_status,
    update_order_refund_status,
)

# Kills the task if it recurses more than 10000 times (=> 10M rows),
# something is likely wrong if it does. Assuming 1 task = 1sec, it would
# take ~3 hours to abort.
BACKFILL_ORDER_STATUSES_MAX_DEPTH = 10000
BACKFILL_ORDER_STATUSES_BATCH_SIZE = 1000


task_logger = get_task_logger(f"{__name__}.celery")


@app.task(queue=settings.DATA_MIGRATIONS_TASKS_QUEUE_NAME)
@allow_writer()
def backfill_order_statuses(
    current_depth: int,
    last_order_pk: int | None = None,
    max_depth: int = BACKFILL_ORDER_STATUSES_MAX_DEPTH,
):
    """Set the refund and the charge status for the orders that already have refunds.

    The statuses are derived from the refunded and the charged amount of the order,
    matching how ``update_order_refund_status`` and ``update_order_charge_status``
    calculate them. A refund that is still processed by the payment app counts as well,
    so the status does not change once the refund is reported as successful.

    The charge status is recalculated as well: an order with nothing charged left and a
    granted refund covering the whole total was previously reported as fully charged,
    although it is refunded.
    """
    if current_depth > max_depth:
        raise RecursionError(
            f"Data migration for the order statuses has recursed {current_depth} times. "
            "Is the job stuck? Please check the database whether there are too many "
            "orders to process (see the queryset in the Python code for reference). "
            "Rerun this task manually if there is a lot of data to process, you can also "
            "override the ``max_depth`` to allow this task to recurse deeper."
        )

    with transaction.atomic():
        orders = _get_locked_orders_batch(last_order_pk)
        if not orders:
            return

        for order in orders:
            order_payments = order.payments.all()
            order_transactions = order.payment_transactions.all()
            total_charged = _get_total_charged(order_payments, order_transactions)
            total_refunded = _get_total_refunded(order_payments, order_transactions)
            total_refund_pending = _get_total_refund_pending(order_transactions)
            refunded_amount = total_refunded + total_refund_pending

            update_order_refund_status(
                order,
                total_refunded=refunded_amount,
                total_charged=_get_total_charged_before_refunds(
                    order_payments, total_charged, refunded_amount
                ),
            )
            update_order_charge_status(
                order,
                _get_granted_refunds_amount(order),
                refunded_amount,
            )
        Order.objects.bulk_update(orders, ["refund_status", "charge_status"])

    task_logger.info("Backfilled the statuses of %d orders", len(orders))

    if len(orders) == BACKFILL_ORDER_STATUSES_BATCH_SIZE:
        backfill_order_statuses.delay(
            current_depth=current_depth + 1,
            last_order_pk=orders[-1].pk,
            max_depth=max_depth,
        )


def _get_locked_orders_batch(last_order_pk: int | None) -> list[Order]:
    """Return the batch of orders to backfill, locked against concurrent runs.

    The orders are processed from the newest to the oldest, as the zero-downtime policy
    requires, so the orders that are placed recently are corrected first. The rows are
    locked in that order, so the workers running the task at the same time cannot
    deadlock on them. Has to be called inside a transaction.
    """
    queryset: QuerySet[Order] = (
        order_qs_select_for_update()
        .prefetch_related(
            "payments__transactions", "payment_transactions", "granted_refunds"
        )
        .order_by("-pk")
    )
    if last_order_pk is not None:
        queryset = queryset.filter(pk__lt=last_order_pk)
    return list(queryset[:BACKFILL_ORDER_STATUSES_BATCH_SIZE])


def _get_granted_refunds_amount(order: Order) -> Decimal:
    return sum(
        (granted_refund.amount_value for granted_refund in order.granted_refunds.all()),
        Decimal(0),
    )
