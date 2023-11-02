from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_13 import update_orders_charge_statuses_task


def update_orders_charge_statuses(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        update_orders_charge_statuses_task.delay()

    sender = registry.get_app_config("order")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0164_auto_20230329_1200"),
    ]
    operations = [
        migrations.RunPython(
            update_orders_charge_statuses, reverse_code=migrations.RunPython.noop
        ),
    ]
