# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='productimage',
            name='order',
            field=models.PositiveIntegerField(default=0, editable=False),
            preserve_default=False,
        ),
    ]
