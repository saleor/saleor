from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_19 import fix_invalid_atobarai_payments_task


def fix_invalid_atobarai_payments(apps, schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        fix_invalid_atobarai_payments_task.delay()

    sender = registry.get_app_config("payment")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0055_add_constraints_from_indexes"),
    ]

    operations = [
        migrations.RunPython(fix_invalid_atobarai_payments, migrations.RunPython.noop),
    ]
