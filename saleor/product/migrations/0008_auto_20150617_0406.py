# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0007_auto_20150616_0852'),
    ]

    operations = [
        migrations.AddField(
            model_name='stock',
            name='quantity',
            field=models.IntegerField(default=Decimal('1'), verbose_name='quantity', validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='stock',
            name='product',
            field=models.ForeignKey(editable=False, to='product.Product', verbose_name='product'),
        ),
        migrations.AlterUniqueTogether(
            name='stock',
            unique_together=set([('product', 'variant', 'location')]),
        ),
        migrations.RemoveField(
            model_name='stock',
            name='stock',
        ),
    ]
