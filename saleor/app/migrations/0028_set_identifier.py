from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_14 import (
    set_identifier_for_local_apps_task,
    set_identifier_for_local_apps_task_with_none_global_id,
)


# Fixes the issue from previous identifier changes, where `app_create` was setting
# identifier based on NULL PK
# Need to rerun migration task from migration 0027 cause of missing
# setting up `identifier` on create_app command


def set_identifier_for_local_apps(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        set_identifier_for_local_apps_task.delay()
        set_identifier_for_local_apps_task_with_none_global_id.delay()

    sender = registry.get_app_config("app")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0027_set_identifier_when_missing"),
    ]

    operations = [
        migrations.RunPython(set_identifier_for_local_apps, migrations.RunPython.noop),
    ]
