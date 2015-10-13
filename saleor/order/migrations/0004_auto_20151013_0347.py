# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_auto_20150825_1433'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='currency',
            field=models.CharField(default=b'USD', max_length=3, verbose_name='currency'),
        ),
        migrations.AddField(
            model_name='order',
            name='rate',
            field=models.DecimalField(default=0, verbose_name='conversion rate', max_digits=12, decimal_places=5),
        ),
    ]
