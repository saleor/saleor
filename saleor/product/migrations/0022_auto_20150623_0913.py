# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0021_auto_20150623_0902'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attributechoicevalue',
            name='color',
            field=models.CharField(blank=True, max_length=7, validators=[django.core.validators.RegexValidator('^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')]),
        ),
    ]
