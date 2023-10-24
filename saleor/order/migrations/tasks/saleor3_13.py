from decimal import Decimal

from babel.numbers import get_currency_precision
from django.db import transaction
from django.db.models import QuerySet
from django.db.models.expressions import Exists, OuterRef

from ....celeryconf import app
from ... import OrderChargeStatus
from ...models import Order, OrderEvent, OrderGrantedRefund

# Batch size of size 5000 is about 3MB memory usage in task
BATCH_SIZE = 5000


def update_type_to_transaction_cancel_requested(qs: QuerySet[OrderEvent]):
    with transaction.atomic():
        # lock the batch of objects
        _events = list(qs.select_for_update(of=(["self"])))
        qs.update(type="transaction_cancel_requested")


@app.task
def order_events_rename_transaction_void_events_task():
    events = OrderEvent.objects.filter(type="transaction_void_requested").order_by(
        "-pk"
    )
    ids = events.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = OrderEvent.objects.filter(pk__in=ids)

    if ids:
        update_type_to_transaction_cancel_requested(qs)
        order_events_rename_transaction_void_events_task.delay()


def update_type_to_transaction_charge_requested(qs: QuerySet[OrderEvent]):
    with transaction.atomic():
        # lock the batch of objects
        _events = list(qs.select_for_update(of=(["self"])))
        qs.update(type="transaction_charge_requested")


@app.task
def order_events_rename_transaction_capture_events_task():
    events = OrderEvent.objects.filter(type="transaction_capture_requested").order_by(
        "-pk"
    )
    ids = events.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = OrderEvent.objects.filter(pk__in=ids)

    if ids:
        update_type_to_transaction_charge_requested(qs)
        order_events_rename_transaction_capture_events_task.delay()


def quantize_price(price, currency: str):
    precision = get_currency_precision(currency)
    number_places = Decimal(10) ** -precision
    return price.quantize(number_places)


def update_order_charge_status(order: Order, granted_refund_amount: Decimal):
    """Update the current charge status for the order.

    We treat the order as overcharged when the charged amount is bigger that
    order.total - order granted refund
    We treat the order as fully charged when the charged amount is equal to
    order.total - order granted refund.
    We treat the order as partially charged when the charged amount covers only part of
    the order.total - order granted refund
    We treat the order as not charged when the charged amount is 0.
    """
    total_charged = order.total_charged_amount or Decimal("0")
    total_charged = quantize_price(total_charged, order.currency)

    current_total_gross = order.total_gross_amount - granted_refund_amount
    current_total_gross = max(current_total_gross, Decimal("0"))
    current_total_gross = quantize_price(current_total_gross, order.currency)

    if total_charged == current_total_gross:
        order.charge_status = OrderChargeStatus.FULL
    elif total_charged <= Decimal(0):
        order.charge_status = OrderChargeStatus.NONE
    elif total_charged < current_total_gross:
        order.charge_status = OrderChargeStatus.PARTIAL
    else:
        order.charge_status = OrderChargeStatus.OVERCHARGED


@app.task
def update_orders_charge_statuses_task(stop_granted_refund_pk=-1):
    """Update the charge status for orders with granted refunds.

    Task takes around 0.3 seconds for 1000 orders and around 5 MB of memory.
    """
    if stop_granted_refund_pk == -1:
        stop_granted_refund_pk = OrderGrantedRefund.objects.count()
    order_charge_status_batch_size = 1000
    start_pk = stop_granted_refund_pk - order_charge_status_batch_size
    stop_pk = stop_granted_refund_pk
    orders = Order.objects.filter(
        Exists(
            OrderGrantedRefund.objects.filter(
                order_id=OuterRef("pk"),
                pk__gte=start_pk,
                pk__lt=stop_pk,
            )
        )
    ).prefetch_related("granted_refunds")
    orders_to_update = []
    for o in orders:
        granted_refund_amount = sum(
            [refund.amount.amount for refund in o.granted_refunds.all()], Decimal(0)
        )
        update_order_charge_status(o, granted_refund_amount)
        orders_to_update.append(o)

    if orders_to_update:
        Order.objects.bulk_update(orders_to_update, ["charge_status"])
        update_orders_charge_statuses_task.delay(start_pk)
