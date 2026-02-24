from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_22 import populate_order_gift_card_applications_task


def schedule_task(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        populate_order_gift_card_applications_task.delay()

    sender = registry.get_app_config("order")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [("order", "0220_ordergiftcardapplication")]

    operations = [
        migrations.RunPython(schedule_task, reverse_code=migrations.RunPython.noop)
    ]
