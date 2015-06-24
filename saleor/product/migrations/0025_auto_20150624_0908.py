# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0024_remove_product_collection'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productvariant',
            name='attributes',
            field=jsonfield.fields.JSONField(default={}, verbose_name='attributes', blank=True),
        ),
    ]
