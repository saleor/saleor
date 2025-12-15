from django.db.models import Exists, OuterRef

from ....celeryconf import app
from ...models import Order, OrderLine, OrderStatus

# Takes about 0.1 second to process
DUPLICATED_LINES_ORDER_BATCH_SIZE = 200


@app.task
def clean_duplicated_gift_lines_task(created_after=None):
    extra_filter = {}
    if created_after:
        extra_filter["created_at__gt"] = created_after

    order_data = list(
        Order.objects.filter(
            status=OrderStatus.DRAFT,
        )
        .filter(
            Exists(
                OrderLine.objects.filter(is_gift=True).filter(order_id=OuterRef("pk"))
            )
        )
        .order_by("created_at")
        .filter(**extra_filter)
        .values_list("pk", "created_at")[:DUPLICATED_LINES_ORDER_BATCH_SIZE]
    )
    order_ids = [data[0] for data in order_data]
    if not order_ids:
        return

    order_created_after = order_data[-1][1]
    lines = OrderLine.objects.filter(order_id__in=order_ids, is_gift=True).order_by(
        "order_id", "id"
    )
    seen_orders = set()
    lines_to_delete = []
    for line in lines:
        if line.order_id in seen_orders:
            lines_to_delete.append(line.id)
        else:
            seen_orders.add(line.order_id)

    OrderLine.objects.filter(id__in=lines_to_delete).delete()
    clean_duplicated_gift_lines_task.delay(created_after=order_created_after)
