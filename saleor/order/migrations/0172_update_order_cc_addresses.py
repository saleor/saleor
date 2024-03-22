from django.db import migrations
from django.apps import apps as registry
from django.db.models.signals import post_migrate
from .tasks.saleor3_14 import update_order_addresses_task


def update_order_addresses(apps, schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        update_order_addresses_task.delay()

    sender = registry.get_app_config("order")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0171_order_order_user_email_user_id_idx"),
    ]

    operations = [
        migrations.RunPython(update_order_addresses, migrations.RunPython.noop),
    ]
