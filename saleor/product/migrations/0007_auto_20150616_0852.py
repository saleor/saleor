# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import django.core.validators
import django_prices.models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0006_auto_20150616_0647'),
    ]

    operations = [
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stock', models.IntegerField(default=Decimal('1'), verbose_name='stock', validators=[django.core.validators.MinValueValidator(0)])),
                ('location', models.CharField(max_length=100, verbose_name='location')),
                ('cost_price', django_prices.models.PriceField(decimal_places=4, currency=b'USD', max_digits=12, blank=True, null=True, verbose_name='cost price')),
                ('product', models.ForeignKey(verbose_name='product', to='product.Product')),
                ('variant', models.ForeignKey(verbose_name='variant', blank=True, to='product.ProductVariant', null=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='stock',
            unique_together=set([('product', 'variant', 'stock')]),
        ),
    ]
