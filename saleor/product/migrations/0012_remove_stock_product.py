# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0011_auto_20150618_0938'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stock',
            name='product',
        ),
    ]
