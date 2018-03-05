# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_prices.models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_auto_20150825_1433'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='total',
            field=django_prices.models.MoneyField(decimal_places=2, currency='USD', max_digits=12, blank=True, null=True, verbose_name='total'),
        ),
    ]
