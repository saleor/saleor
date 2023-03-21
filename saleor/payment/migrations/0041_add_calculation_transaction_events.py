from django.db import migrations
from django.apps import apps as registry
from django.db.models.signals import post_migrate

from .tasks.saleor3_12 import (
    create_event_for_authorized,
    create_event_for_canceled,
    create_event_for_charged,
    create_event_for_refunded,
)


def create_transaction_events(apps, schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        create_event_for_authorized.delay()
        create_event_for_canceled.delay()
        create_event_for_charged.delay()
        create_event_for_refunded.delay()

    sender = registry.get_app_config("payment")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0040_migrate_renamed_fields"),
    ]

    operations = [
        migrations.RunPython(create_transaction_events, migrations.RunPython.noop),
    ]
