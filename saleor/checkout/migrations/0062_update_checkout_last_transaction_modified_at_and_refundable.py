from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_14 import (
    update_checkout_refundable,
    update_transaction_modified_at_in_checkouts,
)


def add_transaction_modified_at_to_checkouts(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        update_transaction_modified_at_in_checkouts.delay()

    sender = registry.get_app_config("checkout")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


def calculate_checkout_refundable(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        update_checkout_refundable.delay()

    sender = registry.get_app_config("checkout")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("checkout", "0061_checkout_last_transaction_modified_at_and_refundable"),
    ]

    operations = [
        migrations.RunPython(
            add_transaction_modified_at_to_checkouts,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            calculate_checkout_refundable,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
