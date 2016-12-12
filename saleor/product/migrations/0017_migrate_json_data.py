from __future__ import unicode_literals

import json

from django.db import migrations


def move_data(apps, schema_editor):
    ProductVariant = apps.get_model('product', 'ProductVariant')

    for variant in ProductVariant.objects.all():
        if isinstance(variant.attributes, dict):
            variant.attributes_postgres = variant.attributes
        else:
            variant.attributes_postgres = json.loads(variant.attributes)
        variant.save()


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0016_auto_20161211_1912'),
    ]

    operations = [
        migrations.RunPython(move_data),
        migrations.RemoveField(
            model_name='productvariant',
            name='attributes',
        ),
        migrations.RenameField(
            model_name='productvariant',
            old_name='attributes_postgres',
            new_name='attributes',
        ),
    ]
