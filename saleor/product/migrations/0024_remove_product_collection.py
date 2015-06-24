# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0023_auto_20150624_0741'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='collection',
        ),
    ]
