from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate


def wrong_app_config(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        pass

    # ruleid: django-migration-wrong-app-config
    sender = registry.get_app_config("attribute")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


def correct_app_config(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        pass

    # ok: django-migration-wrong-app-config
    sender = registry.get_app_config("order")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


def wrong_app_config_multiline(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        pass

    # ruleid: django-migration-wrong-app-config
    sender = registry.get_app_config(
        "attribute"
    )
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


def correct_app_config_multiline(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        pass

    # ok: django-migration-wrong-app-config
    sender = registry.get_app_config(
        "order"
    )
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0219_merge"),
    ]

    operations = [
        migrations.RunPython(wrong_app_config, migrations.RunPython.noop),
        migrations.RunPython(correct_app_config, migrations.RunPython.noop),
    ]
