from ....celeryconf import app
from ...models import OrderEvent

# Batch size of size 1000 is about 1MB memory usage in task
BATCH_SIZE = 1000


@app.task
def order_eventes_rename_transaction_void_events():
    qs = OrderEvent.objects.filter(type="transaction_void_requested").order_by("pk")
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    if ids:
        OrderEvent.objects.filter(pk__in=ids).update(
            type="transaction_cancel_requested"
        )

        del ids
        order_eventes_rename_transaction_void_events.delay()


@app.task
def order_eventes_rename_transaction_capture_events():
    qs = OrderEvent.objects.filter(type="transaction_capture_requested").order_by("pk")
    ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    if ids:
        OrderEvent.objects.filter(pk__in=ids).update(
            type="transaction_charge_requested"
        )

        del ids
        order_eventes_rename_transaction_capture_events.delay()
