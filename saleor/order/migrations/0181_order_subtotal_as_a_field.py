from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_19 import update_order_subtotals


def trigger_update_order_subtotals(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        update_order_subtotals.delay()

    sender = registry.get_app_config("order")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0180_auto_20231108_0908"),
    ]

    operations = [
        migrations.RunPython(
            trigger_update_order_subtotals, reverse_code=migrations.RunPython.noop
        ),
    ]
