from django.db import migrations
from django.apps import apps as registry
from django.db.models.signals import post_migrate

from .tasks.saleor3_13 import (
    order_eventes_rename_transaction_capture_events,
    order_eventes_rename_transaction_void_events,
)


def rename_order_events(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        OrderEvent = apps.get_model("order", "OrderEvent")
        if OrderEvent.objects.filter(type="transaction_void_requested").exists():
            order_eventes_rename_transaction_void_events.delay()
        if OrderEvent.objects.filter(type="transaction_capture_requested").exists():
            order_eventes_rename_transaction_capture_events.delay()

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
