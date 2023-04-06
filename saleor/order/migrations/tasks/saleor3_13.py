from ....celeryconf import app
from ...models import OrderEvent

from django.db import transaction
from django.db.models import QuerySet

# Batch size of size 5000 is about 1MB memory usage in task
BATCH_SIZE = 5000


def update_type_to_transaction_cancel_requested(qs: QuerySet[OrderEvent]):
    with transaction.atomic():
        # lock the batch of objects
        _events = list(qs.select_for_update(of=(["self"])))
        qs.update(type="transaction_cancel_requested")


@app.task
def order_events_rename_transaction_void_events_task():
    qs = OrderEvent.objects.filter(type="transaction_void_requested").order_by("-pk")
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = qs.filter(pk__in=ids)

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
    qs = OrderEvent.objects.filter(type="transaction_capture_requested").order_by("-pk")
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = qs.filter(pk__in=ids)

    if ids:
        update_type_to_transaction_charge_requested(qs)
        order_events_rename_transaction_capture_events_task.delay()
