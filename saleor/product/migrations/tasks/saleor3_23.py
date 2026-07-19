from django.conf import settings
from django.db import transaction

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ...lock_objects import product_qs_select_for_update
from ...models import Product

# One batch updates took ~0.5s
BATCH_SIZE = 5000


@app.task(queue=settings.DATA_MIGRATIONS_TASKS_QUEUE_NAME)
@allow_writer()
def mark_products_search_index_as_dirty_task():
    product_pks = list(
        Product.objects.filter(search_index_dirty=False)
        .order_by("pk")
        .values_list("pk", flat=True)[:BATCH_SIZE]
    )
    if not product_pks:
        return

    with transaction.atomic():
        pks = (
            product_qs_select_for_update()
            .filter(pk__in=product_pks)
            .values_list("pk", flat=True)
        )
        Product.objects.filter(pk__in=pks).update(search_index_dirty=True)
    mark_products_search_index_as_dirty_task.delay()
