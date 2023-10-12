from django.db import migrations
from django.apps import apps as registry
from django.db.models.signals import post_migrate

from .tasks.saleor3_18 import recalculate_undiscounted_prices


def recalculate_undiscounted_prices_for_order(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        recalculate_undiscounted_prices.delay()

    sender = registry.get_app_config("order")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0174_order_idx_order_created_at"),
    ]

    operations = [
        migrations.RunPython(
            recalculate_undiscounted_prices_for_order,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
