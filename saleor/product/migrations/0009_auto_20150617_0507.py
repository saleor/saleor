# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0008_auto_20150617_0406'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='genericproduct',
            name='stock',
        ),
        migrations.RemoveField(
            model_name='genericvariant',
            name='stock',
        ),
        migrations.AlterField(
            model_name='stock',
            name='product',
            field=models.ForeignKey(related_name='stock', verbose_name='product', to='product.Product'),
        ),
        migrations.AlterField(
            model_name='stock',
            name='variant',
            field=models.ForeignKey(related_name='stock', verbose_name='variant', blank=True, to='product.ProductVariant', null=True),
        ),
    ]
