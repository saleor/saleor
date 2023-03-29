from django.db import migrations
from django.apps import apps as registry
from django.db.models.signals import post_migrate

from .tasks.saleor3_13 import (
    order_events_rename_transaction_capture_events_task,
    order_events_rename_transaction_void_events_task,
)


def rename_order_events(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        order_events_rename_transaction_void_events_task.delay()
        order_events_rename_transaction_capture_events_task.delay()

    sender = registry.get_app_config("order")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0162_order_granted_refund"),
    ]
    operations = [
        migrations.RunPython(
            rename_order_events, reverse_code=migrations.RunPython.noop
        ),
    ]
