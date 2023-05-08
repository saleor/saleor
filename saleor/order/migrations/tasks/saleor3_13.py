from ....celeryconf import app
from ...models import OrderEvent, Order

from django.db import transaction
from django.db.models import F, QuerySet

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


def update_number_as_str(qs: QuerySet[Order]):
    with transaction.atomic():
        # lock the batch of objects
        _orders = list(qs.select_for_update(of=(["self"])))
        qs.update(number_as_str=F("number"))


@app.task
def order_update_number_as_str_task():
    orders = Order.objects.filter(number_as_str__isnull=True).order_by("-created_at")
    ids = orders.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = Order.objects.filter(pk__in=ids)

    if qs:
        update_number_as_str(qs)
        order_update_number_as_str_task.delay()
