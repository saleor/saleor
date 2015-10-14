# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def add_orders_to_items(apps, schema_editor):
    OrderedItem = apps.get_model('order', 'OrderedItem')

    for item in OrderedItem.objects.all():
        item.order = item.delivery_group.order
        item.save()

class Migration(migrations.Migration):

    dependencies = [
        ('order', '0005_ordereditem_order'),
    ]

    operations = [
        migrations.RunPython(add_orders_to_items)
    ]
