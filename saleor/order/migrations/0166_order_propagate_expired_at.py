from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_14 import order_propagate_expired_at_task


def propagate_order_expired_at(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        order_propagate_expired_at_task.delay()

    sender = registry.get_app_config("order")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0165_order_expired_at"),
    ]
    operations = [
        migrations.RunPython(
            propagate_order_expired_at, reverse_code=migrations.RunPython.noop
        ),
    ]
