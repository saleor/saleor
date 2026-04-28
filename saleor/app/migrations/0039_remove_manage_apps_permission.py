from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_24 import (
    remove_manage_apps_permission_from_app_extensions_task,
    remove_manage_apps_permission_from_apps_task,
)


def remove_manage_apps_permission(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        remove_manage_apps_permission_from_apps_task.delay()
        remove_manage_apps_permission_from_app_extensions_task.delay()

    sender = registry.get_app_config("app")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0038_merge_20260213_1154"),
    ]

    operations = [
        migrations.RunPython(remove_manage_apps_permission, migrations.RunPython.noop),
    ]
