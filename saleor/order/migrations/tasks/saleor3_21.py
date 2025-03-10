from datetime import timedelta

from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils import timezone

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ...models import Order, OrderLine

# The batch of size 250 takes ~0.2 second and consumes ~20MB memory at peak
BATCH_SIZE = 250
DEFAULT_EXPIRE_TIME = 24


@app.task
@allow_writer()
def set_base_price_expire_time_task():
    orders = Order.objects.filter(status="draft")
    qs = (
        OrderLine.objects.filter(Exists(orders.filter(pk=OuterRef("order_id"))))
        .filter(draft_base_price_expire_at__isnull=True)
        .order_by("pk")
    )
    line_ids = qs.values_list("pk", flat=True)[:BATCH_SIZE]
    if line_ids:
        order_lines = OrderLine.objects.filter(id__in=line_ids).order_by("pk")
        now = timezone.now()
        expire_time = now + timedelta(hours=DEFAULT_EXPIRE_TIME)
        with transaction.atomic():
            _order_lines_lock = list(order_lines.select_for_update(of=(["self"])))
            order_lines.update(draft_base_price_expire_at=expire_time)

        set_base_price_expire_time_task.delay()
