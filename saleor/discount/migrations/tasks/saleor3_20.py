from django.db.models import OuterRef, Subquery

from ....celeryconf import app
from ...models import OrderDiscount

# The batch of size 5000 takes ~0.1 second and consumes ~4MB memory at peak
BATCH_SIZE = 5000


@app.task
def set_discount_currency_task(start_id=0):
    ids = list(
        OrderDiscount.objects.filter(currency="")
        .order_by("id")
        .filter(id__gt=start_id)[:BATCH_SIZE]
        .values_list("id", flat=True)
    )
    if ids:
        qs = (
            OrderDiscount.objects.filter(id__in=ids)
            .filter(id__gt=start_id)
            .select_related("order")
            .order_by("id")
            .only("id", "currency", "order__currency")
        )
        qs.update(
            currency=Subquery(
                OrderDiscount.objects.filter(pk=OuterRef("id")).values(
                    "order__currency"
                )[:1]
            )
        )
        start_id = ids[-1]
        set_discount_currency_task.delay(start_id)
