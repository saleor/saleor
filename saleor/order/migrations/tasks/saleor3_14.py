from django.utils import timezone

from ....celeryconf import app
from ... import OrderStatus
from ...models import Order

# Batch size of size 5000 is about 5MB memory usage in task
BATCH_SIZE = 5000


@app.task
def order_propagate_expired_at_task():
    qs = Order.objects.filter(status=OrderStatus.EXPIRED, expired_at__isnull=True)
    order_ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    if order_ids:
        Order.objects.filter(id__in=order_ids).update(expired_at=timezone.now())
        order_propagate_expired_at_task.delay()
