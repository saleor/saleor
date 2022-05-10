from django.db import migrations
from django.db.models.signals import post_migrate

from ...core.search_tasks import set_product_search_document_values


def update_product_search_document_values(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        set_product_search_document_values.delay()

    post_migrate.connect(on_migrations_complete, weak=False)


class Migration(migrations.Migration):

    dependencies = [
        ("product", "0164_auto_20220311_1430"),
    ]

    operations = [
        migrations.RunPython(
            update_product_search_document_values,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
