# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_prices.models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0012_remove_stock_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='price',
            field=django_prices.models.PriceField(decimal_places=4, currency=b'USD', max_digits=12, blank=True, null=True, verbose_name='price'),
        ),
    ]
