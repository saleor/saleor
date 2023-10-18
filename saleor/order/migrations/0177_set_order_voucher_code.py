from django.db import migrations
from .tasks.saleor3_17 import set_order_voucher_code_task
from django.db.models.signals import post_migrate
from django.apps import apps as registry


def set_order_voucher_code(apps, schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        set_order_voucher_code_task.delay()

    sender = registry.get_app_config("discount")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("discount", "0060_set_vouchercustomer_codes"),
        ("order", "0176_order_voucher_code_add_index"),
    ]

    operations = [
        migrations.RunPython(
            set_order_voucher_code,
            migrations.RunPython.noop,
        ),
    ]
