from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate
from .tasks.saleor3_13 import update_discounted_prices_task


def calculate_variants_discounted_price(apps, schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        update_discounted_prices_task.delay()

    sender = registry.get_app_config("product")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0182_productvariantchannellisting_discounted_price_amount"),
    ]

    operations = [
        migrations.RunPython(
            calculate_variants_discounted_price, migrations.RunPython.noop
        ),
    ]
