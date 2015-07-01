# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0031_auto_20150625_0803'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productattribute',
            options={'ordering': ['name']},
        ),
        migrations.RemoveField(
            model_name='productattribute',
            name='slug',
        ),
        migrations.AddField(
            model_name='productattribute',
            name='name',
            field=models.SlugField(default='', verbose_name='name'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='productattribute',
            name='display',
            field=models.CharField(max_length=100, verbose_name='display'),
        ),
    ]
