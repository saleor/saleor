from django.db import migrations
from django.apps import apps as registry
from django.db.models.signals import post_migrate

from .tasks.saleor3_12 import (
    set_default_currency_for_transaction_event_task,
)


def set_default_currency_for_transaction_event_migration(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        set_default_currency_for_transaction_event_task.delay()

    sender = registry.get_app_config("payment")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0038_auto_20230223_0926"),
    ]

    operations = [
        migrations.RunPython(
            set_default_currency_for_transaction_event_migration,
            migrations.RunPython.noop,
        ),
    ]
