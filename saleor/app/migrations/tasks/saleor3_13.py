from django.contrib.postgres.functions import RandomUUID
from django.db import transaction
from django.db.models import Case, F, When

from ....celeryconf import app
from ...models import App, AppInstallation

BATCH_SIZE = 1000


def update_uuid_field(model_cls, batch_size: int) -> bool:
    qs = model_cls.objects.filter(uuid__isnull=True).order_by("-pk")
    ids = qs.values_list("id", flat=True)[:batch_size]
    if not ids:
        return True
    qs = qs.filter(id__in=ids)
    with transaction.atomic():
        # lock the batch of objects
        _objects = list(qs.select_for_update(of=(["self"])))
        qs.update(
            uuid=Case(When(uuid__isnull=True, then=RandomUUID()), default=F("uuid"))
        )
    return False


@app.task
def update_app_uuid_field_task():
    fully_processed = update_uuid_field(App, BATCH_SIZE)
    if not fully_processed:
        update_app_uuid_field_task.delay()


@app.task
def update_app_installation_uuid_field_task():
    fully_processed = update_uuid_field(AppInstallation, BATCH_SIZE)
    if not fully_processed:
        update_app_installation_uuid_field_task.delay()
