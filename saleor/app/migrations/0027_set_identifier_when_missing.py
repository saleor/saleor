from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_14 import set_identifier_for_local_apps_task


def set_identifier_for_local_apps(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        set_identifier_for_local_apps_task.delay()

    sender = registry.get_app_config("app")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0026_app_removed_at"),
        ("payment", "0055_add_constraints_from_indexes"),
    ]

    operations = [
        migrations.RunPython(set_identifier_for_local_apps, migrations.RunPython.noop),
    ]
