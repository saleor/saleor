# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0019_auto_20150623_0704'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productattribute',
            name='display',
            field=models.CharField(unique=True, max_length=100),
        ),
    ]
