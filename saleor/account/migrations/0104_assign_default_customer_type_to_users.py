from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_23 import assign_default_customer_type_to_users_task


def assign_default_customer_type_to_users(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        assign_default_customer_type_to_users_task.delay()

    sender = registry.get_app_config("account")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0103_create_default_customer_type"),
    ]
    operations = [
        migrations.RunPython(
            assign_default_customer_type_to_users, migrations.RunPython.noop
        ),
    ]
