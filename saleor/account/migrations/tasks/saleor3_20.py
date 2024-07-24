from django.db import transaction
from django.db.models.expressions import Value
from django.db.models.functions import Concat

from ....celeryconf import app
from ...models import User

# in order not to lock the table for too long, we will update the full_name in batches
FULL_NAME_BATCH_SIZE = 1000


def _fill_full_name_for_ids(ids):
    with transaction.atomic():
        User.objects.select_for_update(of=("self",)).filter(id__in=ids).update(
            full_name=Concat("first_name", Value(" "), "last_name")
        )


@app.task
def fill_full_name_task(*args, **kwargs):
    ids = (
        User.objects.order_by("pk")
        .filter(full_name="")
        .exclude(first_name="", last_name="")
        .values_list("id", flat=True)[:FULL_NAME_BATCH_SIZE]
    )

    if ids:
        _fill_full_name_for_ids(ids)
        fill_full_name_task.delay()
