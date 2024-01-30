from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from ..tasks import set_discount_type_to_promotion_catalogue_task


def update_order_line_discount_type(_apps, _schema_editor):
    def on_migrations_complete():
        set_discount_type_to_promotion_catalogue_task.delay()

    sender = registry.get_app_config("discount")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("discount", "0073_auto_20231213_1535"),
    ]

    operations = [
        migrations.RunPython(
            update_order_line_discount_type, reverse_code=migrations.RunPython.noop
        ),
    ]
