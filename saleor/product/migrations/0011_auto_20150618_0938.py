# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0010_genericvariant_weight'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='price',
        ),
        migrations.RemoveField(
            model_name='product',
            name='sku',
        ),
        migrations.AlterField(
            model_name='stock',
            name='variant',
            field=models.ForeignKey(related_name='stock', verbose_name='variant', to='product.ProductVariant'),
        ),
        migrations.AlterUniqueTogether(
            name='stock',
            unique_together=set([('variant', 'location')]),
        ),
    ]
