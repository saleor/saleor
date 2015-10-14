# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0004_auto_20151013_0347'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordereditem',
            name='order',
            field=models.ForeignKey(related_name='items', to='order.Order', null=True),
        ),
    ]
