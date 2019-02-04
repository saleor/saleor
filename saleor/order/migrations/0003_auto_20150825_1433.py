# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations
import django_prices.models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0002_auto_20150820_1955'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deliverygroup',
            name='shipping_price',
            field=django_prices.models.MoneyField(verbose_name='shipping price', decimal_places=4, default=0, currency=settings.DEFAULT_CURRENCY, max_digits=12, editable=False),
        ),
        migrations.AlterField(
            model_name='payment',
            name='customer_ip_address',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
    ]
