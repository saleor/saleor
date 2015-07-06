# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0033_auto_20150701_1005'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='hidden',
            field=models.BooleanField(default=False, verbose_name='hidden'),
        ),
        migrations.AlterField(
            model_name='productattribute',
            name='name',
            field=models.SlugField(unique=True, verbose_name='name'),
        ),
    ]
