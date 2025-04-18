from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_21 import migrate_orders_with_waiting_for_approval_fulfillment_task


def migrate_orders_with_waiting_for_approval_fulfillment(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        migrate_orders_with_waiting_for_approval_fulfillment_task.delay()

    sender = registry.get_app_config("order")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0199_set_draft_base_price_expire_at"),
    ]

    operations = [
        migrations.RunPython(
            migrate_orders_with_waiting_for_approval_fulfillment,
            reverse_code=migrations.RunPython.noop,
        )
    ]
