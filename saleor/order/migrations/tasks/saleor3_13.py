from ....celeryconf import app
from ...models import OrderEvent

# Batch size of size 1000 is about 1MB memory usage in task
BATCH_SIZE = 1000


def _get_ids(qs, batch_size=None):
    if batch_size:
        return qs.values_list("pk", flat=True)[:batch_size]
    return qs.values_list("pk", flat=True)


def order_eventes_rename_transaction_void_events(order_event_class, batch_size=None):
    qs = order_event_class.objects.filter(type="transaction_void_requested").order_by(
        "pk"
    )
    ids = _get_ids(qs, batch_size)
    if ids:
        order_event_class.objects.filter(pk__in=ids).update(
            type="transaction_cancel_requested"
        )

        return True
    return False


@app.task
def order_eventes_rename_transaction_void_events_task():
    if order_eventes_rename_transaction_void_events(OrderEvent, BATCH_SIZE):
        order_eventes_rename_transaction_void_events_task.delay()


def order_eventes_rename_transaction_capture_events(order_event_class, batch_size=None):
    qs = order_event_class.objects.filter(
        type="transaction_capture_requested"
    ).order_by("pk")
    ids = _get_ids(qs, batch_size)
    if ids:
        order_event_class.objects.filter(pk__in=ids).update(
            type="transaction_charge_requested"
        )

        return True
    return False


@app.task
def order_eventes_rename_transaction_capture_events_task():
    if order_eventes_rename_transaction_capture_events(OrderEvent, BATCH_SIZE):
        order_eventes_rename_transaction_capture_events_task.delay()
