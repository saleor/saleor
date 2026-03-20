from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_23 import delete_digital_order_events


def delete_legacy_orderevents(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        delete_digital_order_events.delay(current_depth=0)

    sender = registry.get_app_config("order")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0220_update_order_search_vector"),
    ]

    operations = [
        migrations.RunPython(delete_legacy_orderevents, migrations.RunPython.noop),
    ]
