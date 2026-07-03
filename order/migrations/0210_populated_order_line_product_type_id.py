from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_22 import populate_order_line_product_type_id_task


def populate_order_line_product_id(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        populate_order_line_product_type_id_task.delay()

    sender = registry.get_app_config("order")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0209_orderline_product_type_id"),
    ]

    operations = [
        migrations.RunPython(
            populate_order_line_product_id,
            reverse_code=migrations.RunPython.noop,
        )
    ]
