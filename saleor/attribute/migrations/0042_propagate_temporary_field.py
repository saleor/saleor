from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_19 import copy_page_id, copy_product_id


def copy_values_to_temporary_fields(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        copy_page_id.delay()
        copy_product_id.delay()

    sender = registry.get_app_config("attribute")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("attribute", "0041_auto_20240508_0855"),
    ]

    operations = [
        migrations.RunPython(
            copy_values_to_temporary_fields, migrations.RunPython.noop
        ),
    ]
