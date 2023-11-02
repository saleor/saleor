from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_13 import fix_statuses_for_empty_checkouts_task


def fix_charge_status_for_empty_checkouts(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        fix_statuses_for_empty_checkouts_task.delay()

    sender = registry.get_app_config("checkout")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("checkout", "0059_merge_0058"),
    ]
    operations = [
        migrations.RunPython(
            fix_charge_status_for_empty_checkouts,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
