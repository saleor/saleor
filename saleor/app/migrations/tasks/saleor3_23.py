from django.conf import settings
from django.db import transaction
from django.db.models.expressions import RawSQL

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ...models import AppExtension

BATCH_SIZE = 100

# `http_target_method` was dropped from the model state in 3.24 (migration 0043)
# but the column is still there until it is dropped for good. Read it directly so
# this backfill keeps working for instances upgrading straight from 3.22.
LEGACY_HTTP_TARGET_METHOD = RawSQL("http_target_method", ())

TARGET_TO_SETTINGS_KEY = {"WIDGET": "widgetTarget", "NEW_TAB": "newTabTarget"}


@app.task(queue=settings.DATA_MIGRATIONS_TASKS_QUEUE_NAME)
@allow_writer()
def fill_app_extension_settings_task():
    qs = (
        AppExtension.objects.filter(settings={}, target__in=["widget", "new_tab"])
        .annotate(legacy_http_target_method=LEGACY_HTTP_TARGET_METHOD)
        .only("target", "settings")[:BATCH_SIZE]
    )

    with transaction.atomic():
        locked_qs = qs.select_for_update()

        app_extensions = list(locked_qs)
        dirty_extensions: list[AppExtension] = []

        for extension in app_extensions:
            settings_key = TARGET_TO_SETTINGS_KEY.get(extension.target.upper())

            if settings_key:
                extension.settings = {
                    settings_key: {"method": extension.legacy_http_target_method}
                }

                dirty_extensions.append(extension)

        AppExtension.objects.bulk_update(dirty_extensions, fields=["settings"])

    if app_extensions:
        fill_app_extension_settings_task.delay()
