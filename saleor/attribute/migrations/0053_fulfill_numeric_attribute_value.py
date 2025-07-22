from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_22 import fulfill_attribute_value_numeric_field


def set_up_numeric_attribute_values(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        fulfill_attribute_value_numeric_field.delay()

    sender = registry.get_app_config("attribute")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("attribute", "0052_attributevalue_attribute_value_numeric_idx"),
    ]

    operations = [
        migrations.RunPython(
            set_up_numeric_attribute_values,
            reverse_code=migrations.RunPython.noop,
        )
    ]
