from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_15 import drop_status_field_from_transaction_event_task


def drop_status_field_from_transaction_event(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        drop_status_field_from_transaction_event_task.delay()

    sender = registry.get_app_config("order")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0171_alter_orderevent_type"),
    ]

    operations = [
        migrations.RunPython(
            drop_status_field_from_transaction_event,
            reverse_code=migrations.RunPython.noop,
        )
    ]
