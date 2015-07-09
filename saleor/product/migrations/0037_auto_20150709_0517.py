# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0036_auto_20150709_0517'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='available_on',
            field=models.DateField(null=True, verbose_name='available on', blank=True),
        ),
    ]
