from django.db import migrations
from django.db.models import Q

BATCH_SIZE = 100
TARGET_TO_SETTINGS_KEY = {"WIDGET": "widgetTarget", "NEW_TAB": "newTabTarget"}


def fill_app_extension_settings(apps, _schema_editor):
    """Backfill `settings` from the legacy `http_target_method` column.

    3.23 did this from a Celery task scheduled on `post_migrate` (migration
    0035), which never runs if no worker picks it up and records nothing about
    whether it finished. `http_target_method` is dropped from the model state in
    0044 and from the database in a later release, so run the backfill here to
    guarantee it happened first — notably for an instance upgrading straight
    from 3.22, where 0035 is still unapplied.
    """
    AppExtension = apps.get_model("app", "AppExtension")

    while True:
        extensions = list(
            AppExtension.objects.filter(
                Q(target__iexact="widget") | Q(target__iexact="new_tab"),
                settings={},
            )[:BATCH_SIZE]
        )

        if not extensions:
            break

        for extension in extensions:
            settings_key = TARGET_TO_SETTINGS_KEY[extension.target.upper()]
            extension.settings = {
                settings_key: {"method": extension.http_target_method}
            }

        AppExtension.objects.bulk_update(extensions, ["settings"])


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0042_merge_20260820_0919"),
    ]

    operations = [
        migrations.RunPython(fill_app_extension_settings, migrations.RunPython.noop),
    ]
