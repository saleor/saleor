# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0014_auto_20150622_0623'),
    ]

    operations = [
        migrations.DeleteModel(
            name='GenericProduct',
        ),
        migrations.DeleteModel(
            name='GenericVariant',
        ),
    ]
