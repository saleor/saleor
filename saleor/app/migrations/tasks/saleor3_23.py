from django.db import transaction

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ...models import AppExtension

BATCH_SIZE = 100


@app.task
@allow_writer()
def fill_app_extension_settings_task():
    qs = AppExtension.objects.filter(
        settings={}, target__in=["widget", "new_tab"]
    ).only("target", "http_target_method", "settings")[:BATCH_SIZE]

    with transaction.atomic():
        locked_qs = qs.select_for_update()

        app_extensions = list(locked_qs)
        dirty_extensions: list[AppExtension] = []

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

    if app_extensions:
        fill_app_extension_settings_task.delay()
