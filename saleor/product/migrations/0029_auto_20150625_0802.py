# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0028_auto_20150625_0513'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productattribute',
            options={'ordering': ['slug']},
        ),
        migrations.AddField(
            model_name='productattribute',
            name='slug',
            field=models.SlugField(default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='productattribute',
            name='display',
            field=models.CharField(max_length=100),
        ),
    ]
