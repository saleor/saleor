from django.db import migrations
from django.db.models.signals import post_migrate
from django.apps import apps as registry
from .tasks.saleor3_14 import set_user_is_confirmed_task


def set_user_is_confirmed(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        set_user_is_confirmed_task.delay()

    sender = registry.get_app_config("account")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0080_user_is_confirmed"),
    ]

    operations = [
        migrations.RunPython(set_user_is_confirmed, migrations.RunPython.noop)
    ]
