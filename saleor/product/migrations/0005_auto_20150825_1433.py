# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django_prices.models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0004_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fixedproductdiscount',
            name='discount',
            field=django_prices.models.MoneyField(verbose_name='discount value', max_digits=12, decimal_places=2, currency=settings.DEFAULT_CURRENCY),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=django_prices.models.MoneyField(verbose_name='price', max_digits=12, decimal_places=2, currency=settings.DEFAULT_CURRENCY),
        ),
        migrations.AlterField(
            model_name='product',
            name='weight',
            field=models.DecimalField(verbose_name='weight', max_digits=6, decimal_places=2),
        ),
        migrations.AlterField(
            model_name='productvariant',
            name='price_override',
            field=django_prices.models.MoneyField(verbose_name='price override', decimal_places=2, blank=True, currency=settings.DEFAULT_CURRENCY, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='productvariant',
            name='weight_override',
            field=models.DecimalField(verbose_name='weight override', decimal_places=2, blank=True, max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name='stock',
            name='cost_price',
            field=django_prices.models.MoneyField(verbose_name='cost price', decimal_places=2, blank=True, currency=settings.DEFAULT_CURRENCY, max_digits=12, null=True),
        ),
    ]
