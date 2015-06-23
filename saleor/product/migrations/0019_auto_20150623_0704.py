# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0018_auto_20150623_0508'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attributechoicevalue',
            name='name',
        ),
        migrations.RemoveField(
            model_name='productattribute',
            name='name',
        ),
    ]
