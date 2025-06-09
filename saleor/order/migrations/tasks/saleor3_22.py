from django.db import transaction

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ...models import OrderLine

ORDER_LINE_PRODUCT_ID_BATCH_SIZE = 2


@app.task
@allow_writer()
def populate_order_line_product_type_id_task(line_pk=None):
    """Populate product id for order lines."""
    if line_pk is None:
        line_pk = 0
    lines = OrderLine.objects.filter(
        pk__gte=line_pk, variant__isnull=False, product_type_id__isnull=True
    )
    qs = lines.order_by("pk")
    line_pks = list(qs.values_list("pk", flat=True)[:ORDER_LINE_PRODUCT_ID_BATCH_SIZE])
    if line_pks:
        lines = OrderLine.objects.filter(pk__in=line_pks).order_by("pk")
        with transaction.atomic():
            to_save = []
            _lines_lock = list(lines.select_for_update(of=(["self"])))
            for line in lines:
                line.product_type_id = line.variant.product.product_type_id
                to_save.append(line)
            OrderLine.objects.bulk_update(to_save, ["product_type_id"])
        populate_order_line_product_type_id_task.delay(line_pks[-1])
