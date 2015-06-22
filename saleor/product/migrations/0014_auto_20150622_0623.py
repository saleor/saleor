# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_prices.models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0013_product_price'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='genericproduct',
            name='weight',
        ),
        migrations.RemoveField(
            model_name='genericvariant',
            name='weight',
        ),
        migrations.RemoveField(
            model_name='productvariant',
            name='price',
        ),
        migrations.AddField(
            model_name='product',
            name='weight',
            field=models.DecimalField(default=0, verbose_name='weight', max_digits=6, decimal_places=2),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='productvariant',
            name='price_override',
            field=django_prices.models.PriceField(decimal_places=4, currency=b'USD', max_digits=12, blank=True, null=True, verbose_name='price override'),
        ),
        migrations.AddField(
            model_name='productvariant',
            name='weight_override',
            field=models.DecimalField(null=True, verbose_name='weight override', max_digits=6, decimal_places=2, blank=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=django_prices.models.PriceField(default=0, currency=b'USD', verbose_name='price', max_digits=12, decimal_places=4),
            preserve_default=False,
        ),
    ]
