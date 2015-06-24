# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0025_auto_20150624_0908'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productvariant',
            name='attributes',
            field=jsonfield.fields.JSONField(default={}, verbose_name='attributes'),
        ),
    ]
