# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0035_auto_20150709_0345'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='available_on',
            field=models.DateField(verbose_name='available on', blank=True),
        ),
    ]
