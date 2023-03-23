from django.db import migrations
from django.apps import apps as registry
from django.db.models.signals import post_migrate

from .tasks.saleor3_13 import (
    order_eventes_rename_transaction_capture_events,
    order_eventes_rename_transaction_void_events,
    order_eventes_rename_transaction_capture_events_task,
    order_eventes_rename_transaction_void_events_task,
)
from ... import __version__

BATCH_SIZE = 1000


def rename_order_events(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        order_eventes_rename_transaction_void_events_task.delay()
        order_eventes_rename_transaction_capture_events_task.delay()

    if __version__.startswith("3.13"):
        sender = registry.get_app_config("order")
        post_migrate.connect(on_migrations_complete, weak=False, sender=sender)
    else:
        OrderEvent = apps.get_model("order", "OrderEvent")
        result = order_eventes_rename_transaction_void_events(OrderEvent, BATCH_SIZE)
        while result:
            result = order_eventes_rename_transaction_void_events(
                OrderEvent, BATCH_SIZE
            )
        result = order_eventes_rename_transaction_capture_events(OrderEvent, BATCH_SIZE)
        while result:
            result = order_eventes_rename_transaction_capture_events(
                OrderEvent, BATCH_SIZE
            )


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0162_order_granted_refund"),
    ]
    operations = [
        migrations.RunPython(
            rename_order_events, reverse_code=migrations.RunPython.noop
        ),
    ]
