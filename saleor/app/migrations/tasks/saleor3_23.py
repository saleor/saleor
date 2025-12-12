from django.db import transaction
from django.utils import timezone

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ...models import AppExtension

BATCH_SIZE = 100


def fill_settings_json():
    # Preserve filled settings, only migrate if empty (fill them)
    qs = AppExtension.objects.filter(
        settings={}, target__in=["widget", "new_tab"]
    ).only("target", "http_target_method", "settings")[:BATCH_SIZE]

    affected_items = []

    with transaction.atomic():
        qs.select_for_update()

        app_extensions = list(qs)
        dirty_extensions: list[AppExtension] = []

        affected_items = app_extensions

        for extension in app_extensions:
            if extension.target.upper() == "WIDGET":
                extension.settings = {
                    "widgetTarget": {"method": extension.http_target_method}
                }

                dirty_extensions.append(extension)

            if extension.target.upper() == "NEW_TAB":
                extension.settings = {
                    "newTabTarget": {"method": extension.http_target_method}
                }

                dirty_extensions.append(extension)

        AppExtension.objects.bulk_update(dirty_extensions, fields=["settings"])

    if affected_items:
        fill_app_extension_settings_task.delay()


@app.task
@allow_writer()
def fill_app_extension_settings_task():
    start = timezone.now()
    fill_settings_json()

    print(timezone.now() - start)
