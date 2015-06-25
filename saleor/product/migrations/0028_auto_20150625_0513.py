# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_prices.models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0027_auto_20150625_0319'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fixedproductdiscount',
            name='discount',
            field=django_prices.models.PriceField(currency=b'USD', verbose_name='discount value', max_digits=12, decimal_places=2),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=django_prices.models.PriceField(currency=b'USD', verbose_name='price', max_digits=12, decimal_places=2),
        ),
        migrations.AlterField(
            model_name='productvariant',
            name='name',
            field=models.CharField(max_length=100, verbose_name='variant name', blank=True),
        ),
        migrations.AlterField(
            model_name='productvariant',
            name='price_override',
            field=django_prices.models.PriceField(decimal_places=2, currency=b'USD', max_digits=12, blank=True, null=True, verbose_name='price override'),
        ),
        migrations.AlterField(
            model_name='stock',
            name='cost_price',
            field=django_prices.models.PriceField(decimal_places=2, currency=b'USD', max_digits=12, blank=True, null=True, verbose_name='cost price'),
        ),
    ]
