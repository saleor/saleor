# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0037_auto_20150709_0517'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productvariant',
            name='sku',
            field=models.CharField(unique=True, max_length=32, verbose_name='SKU'),
        ),
    ]
