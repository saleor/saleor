# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0009_auto_20150617_0507'),
    ]

    operations = [
        migrations.AddField(
            model_name='genericvariant',
            name='weight',
            field=models.DecimalField(default=1, max_digits=6, decimal_places=2),
            preserve_default=False,
        ),
    ]
