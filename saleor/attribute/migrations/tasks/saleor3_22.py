from django.db import transaction
from django.db.models import F, FloatField
from django.db.models.functions import Cast

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ...models.base import AttributeValue

# Takes around 0.11 seconds to process the batch.
# The memory usage is marginal (~1MB).
BATCH_SIZE = 500


@app.task
@allow_writer()
def fulfill_attribute_value_numeric_field(attribute_value_pk=0):
    value_ids = list(
        AttributeValue.objects.filter(
            pk__gte=attribute_value_pk,
            numeric__isnull=True,
            attribute__input_type="numeric",
        )
        .order_by("pk")
        .values_list("id", flat=True)[:BATCH_SIZE]
    )

    if not value_ids:
        return

    with transaction.atomic():
        locked_values = (
            AttributeValue.objects.filter(id__in=value_ids)
            .order_by("sort_order", "pk")
            .select_for_update()
            .values_list("id", flat=True)
        )
        AttributeValue.objects.filter(id__in=locked_values).update(
            numeric=Cast(F("name"), FloatField())
        )
    fulfill_attribute_value_numeric_field.delay(value_ids[-1])
