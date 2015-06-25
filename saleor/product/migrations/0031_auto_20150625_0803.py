# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0030_auto_20150625_0803'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productattribute',
            name='slug',
            field=models.SlugField(unique=True),
        ),
    ]
