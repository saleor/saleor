from django.db.models import Exists, OuterRef

from ....celeryconf import app
from ....payment.models import TransactionItem
from ...models import OrderEvent

# Batch size of size 5000 is about 5MB memory usage in task
BATCH_SIZE = 5000


@app.task
def drop_status_field_from_transaction_event_task():
    orders = TransactionItem.objects.filter(order_id__isnull=False)

    qs = OrderEvent.objects.filter(
        Exists(orders.filter(order_id=OuterRef("order_id"))),
        type="transaction_event",
        parameters__has_key="status",
    )

    event_ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    if event_ids:
        events_to_update = []
        events = OrderEvent.objects.filter(id__in=event_ids)
        for event in events:
            if "status" in event.parameters:
                del event.parameters["status"]
                events_to_update.append(event)
        OrderEvent.objects.bulk_update(events_to_update, ["parameters"])
        drop_status_field_from_transaction_event_task.delay()
