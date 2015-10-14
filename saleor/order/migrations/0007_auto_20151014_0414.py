# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0006_auto_20151014_0403'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordereditem',
            name='order',
            field=models.ForeignKey(related_name='items', to='order.Order'),
        ),
    ]
