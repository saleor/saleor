# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django_prices.models
from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("order", "0003_auto_20150825_1433")]

    operations = [
        migrations.AddField(
            model_name="order",
            name="total",
            field=django_prices.models.MoneyField(
                decimal_places=2,
                currency=settings.DEFAULT_CURRENCY,
                max_digits=12,
                blank=True,
                null=True,
                verbose_name="total",
            ),
        )
    ]
